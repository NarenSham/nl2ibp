import re
from sqlalchemy.orm import Session
from transformers import pipeline
from models import Promotion, Scenario, FinanceAssumption, SupplyAssumption

# -----------------------------
# Zero-shot intent classifier
# -----------------------------
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# =============================
# Constraint Parser (internal)
# =============================
def constraint_parser(user_input: str) -> list:
    """
    Parse natural language constraints from the user query.
    Returns a list of constraint dicts for backend processing only.
    """
    constraints = []

    # Budget cap (e.g. "under 2M", "below 500k")
    budget = re.search(r"(?:under|below)\s*\$?(\d+[kKmM]?)\s*(?:budget|spend|cost)?", user_input)
    if budget:
        val = budget.group(1).lower()
        multiplier = 1
        if "k" in val:
            multiplier = 1_000
        elif "m" in val:
            multiplier = 1_000_000
        constraints.append({"type": "max_budget", "value": float(re.sub(r'[kKmM]', '', val)) * multiplier})

    # Promotion duration (e.g. "for 2 weeks")
    duration = re.search(r"(?:for|lasting)\s*(\d+)\s*(weeks?|days?|months?)", user_input)
    if duration:
        constraints.append({"type": "promo_duration", "value": f"{duration.group(1)} {duration.group(2)}"})

    # Discount limits
    discount = re.search(r"(?:max|min)?\s*discount\s*(\d+)%", user_input)
    if discount:
        constraints.append({"type": "discount_limit", "value": float(discount.group(1))})

    # Channel restrictions
    channels = {"walmart": "Walmart", "target": "Target"}
    for keyword, channel in channels.items():
        if keyword in user_input.lower():
            constraints.append({"type": "channel_include", "channel": channel})
    if "exclude e-commerce" in user_input.lower() or "no online" in user_input.lower():
        constraints.append({"type": "channel_exclude", "channel": "E-commerce"})

    # SKU / brand restrictions
    sku_focus = re.search(r"(?:only|focus on)\s+([a-zA-Z0-9\s]+)", user_input)
    if sku_focus:
        constraints.append({"type": "sku_focus", "sku": sku_focus.group(1).strip()})
    sku_exclude = re.search(r"exclude\s+([a-zA-Z0-9\s]+)", user_input)
    if sku_exclude:
        constraints.append({"type": "sku_exclude", "sku": sku_exclude.group(1).strip()})

    # ROI / lift targets
    roi = re.search(r"roi\s*>\s*(\d+(\.\d+)?)x", user_input)
    if roi:
        constraints.append({"type": "min_roi", "value": float(roi.group(1))})
    lift = re.search(r"(?:lift|increase)\s*>\s*(\d+)%", user_input)
    if lift:
        constraints.append({"type": "min_lift", "value": float(lift.group(1))})

    return constraints

# =============================
# Main Query Parser
# =============================
def parse_query(user_input: str, db: Session) -> dict:
    """
    Convert user natural language query into structured response + visualization.
    Constraints are extracted internally for backend processing only.
    """
    # --- Extract constraints (internal use) ---
    constraints = constraint_parser(user_input)

    # --- Intent classification ---
    candidate_labels = [
        "list promotions",
        "summarize promotion impact",
        "compare scenarios",
        "show assumptions",
        "what if"
    ]
    classification = classifier(user_input, candidate_labels)
    intent = classification['labels'][0]

    result = {}
    vis = None
    nlg = ""

    # ------------------------
    # 1. List promotions
    # ------------------------
    if intent == "list promotions":
        promos = db.query(Promotion).all()
        result = [
            {
                "promotion_id": p.id,
                "product": p.product.name if p.product else None,
                "retailer": p.retailer.name if p.retailer else None,
                "week": p.week,
                "discount_depth": p.discount_depth,
                "tactic": p.tactic,
                "incremental_units": p.est_incremental_units,
                "incremental_revenue": p.est_incremental_revenue,
                "incremental_profit": p.est_incremental_profit
            }
            for p in promos
        ]
        vis = {"chartType": "table", "data": result}
        nlg = f"I found {len(result)} promotions in the system."

    # ------------------------
    # 2. Summarize promotion impact
    # ------------------------
    elif intent == "summarize promotion impact":
        promos = db.query(Promotion).all()
        result = [
            {
                "promotion": f"{p.product.name} @ {p.retailer.name}",
                "units": p.est_incremental_units or 0,
                "revenue": p.est_incremental_revenue or 0,
                "profit": p.est_incremental_profit or 0
            }
            for p in promos
        ]
        vis = {
            "chartType": "bar",
            "data": [{"promotion": r["promotion"], "revenue": r["revenue"]} for r in result],
            "config": {"x": "promotion", "y": "revenue", "title": "Incremental Revenue by Promotion"}
        }
        nlg = "Here’s the estimated incremental revenue impact by promotion."

    # ------------------------
    # 3. Compare scenarios
    # ------------------------
    elif intent == "compare scenarios":
        scenarios = db.query(Scenario).all()
        result = []
        for s in scenarios:
            revenue = sum(p.promotion.est_incremental_revenue or 0 for p in s.tpo_promotions if p.selected)
            profit = sum(p.promotion.est_incremental_profit or 0 for p in s.tpo_promotions if p.selected)
            result.append({"scenario": s.name, "revenue": revenue, "profit": profit})
        vis = {
            "chartType": "bar",
            "data": result,
            "config": {"x": "scenario", "y": "revenue", "title": "Scenario Comparison (Revenue)"}
        }
        nlg = f"Compared {len(result)} scenarios by revenue and profit."

    # ------------------------
    # 4. Show assumptions
    # ------------------------
    elif intent == "show assumptions":
        assumptions = db.query(FinanceAssumption).all() + db.query(SupplyAssumption).all()
        result = [{"scenario_id": a.scenario_id, "key": a.key, "value": a.value} for a in assumptions]
        vis = {"chartType": "table", "data": result}
        nlg = f"Found {len(result)} finance/supply assumptions across scenarios."

    # ------------------------
    # 5. What-if override
    # ------------------------
    elif intent == "what if":
        match = re.search(r"promotion (\d+).*discount.*(\d+)%", user_input)
        if match:
            promo_id, new_discount = int(match.group(1)), float(match.group(2))
            override = {"promotion_id": promo_id, "new_discount": new_discount}
            result = override
            vis = {"chartType": "table", "data": [override]}
            nlg = f"Applied override: Promotion {promo_id} discount → {new_discount}%"
        else:
            nlg = "Please specify which promotion and new discount you want to test."

    else:
        nlg = "Sorry, I couldn’t interpret your request."

    # ------------------------
    # Return only NLG + visualization + result
    # Constraints stay internal for backend
    # ------------------------
    return {"result": result, "nlg": nlg, "visualization": vis, "constraints": constraints}
