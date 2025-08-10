import torch
from transformers import pipeline
import sqlite3
import re
import math
from .nlg import generate_nlg  # import your NLG function

DB_PATH = "db/optiguide.db"

# Zero-shot classifier
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# ===== Database connection =====
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ===== Constraint Parser =====
def constraint_parser(user_input):
    constraints = []

    # Unavailable warehouses
    unavailable = re.findall(r"warehouse\s*([A-Za-z0-9]+)\s*unavailable", user_input.lower())
    for w in unavailable:
        constraints.append({"type": "exclude_warehouse", "warehouse": w})

    # Max cost
    match = re.search(r"under cost (\d+)", user_input)
    if match:
        constraints.append({"type": "max_cost", "value": float(match.group(1))})

    # Min inventory
    inv_match = re.findall(r"inventory in warehouse\s*([A-Za-z0-9]+)\s*below\s*(\d+)", user_input.lower())
    for w, val in inv_match:
        constraints.append({"type": "min_inventory", "warehouse": w, "value": float(val)})

    return constraints

# ===== Main Query Parser =====
def parse_query(user_input):
    candidate_labels = [
        "list retailers",
        "list warehouses",
        "find routes",
        "calculate demand",
        "what if"
    ]
    classification = classifier(user_input, candidate_labels)
    top_label = classification['labels'][0]

    conn = get_db_connection()
    cursor = conn.cursor()

    if top_label == "list retailers":
        rows = cursor.execute("SELECT * FROM retailers").fetchall()
        conn.close()
        result = [dict(row) for row in rows]
        nlg = generate_nlg(result, intent="list_retailers")
        return {"result": result, "nlg": nlg}

    elif top_label == "list warehouses":
        rows = cursor.execute("SELECT * FROM warehouses").fetchall()
        conn.close()
        result = [dict(row) for row in rows]
        nlg = generate_nlg(result, intent="list_warehouses")
        return {"result": result, "nlg": nlg}

    elif top_label == "find routes":
        match = re.search(r"under cost (\d+)", user_input)
        cost_limit = float(match.group(1)) if match else math.inf
        rows = cursor.execute("SELECT * FROM routes WHERE cost < ?", (cost_limit,)).fetchall()
        conn.close()
        result = [dict(row) for row in rows]
        nlg = generate_nlg(result, intent="find_routes")
        return {"result": result, "nlg": nlg}

    elif top_label == "calculate demand":
        warehouse_name = _find_warehouse_in_text(user_input, conn)
        if not warehouse_name:
            conn.close()
            nlg = "Please specify a warehouse name."
            return {"result": {}, "nlg": nlg}

        w = cursor.execute(
            "SELECT latitude, longitude FROM warehouses WHERE name = ?", (warehouse_name,)
        ).fetchone()
        if not w:
            conn.close()
            nlg = f"No warehouse found with name {warehouse_name}"
            return {"result": {}, "nlg": nlg}

        w_lat, w_lon = w["latitude"], w["longitude"]
        retailers = cursor.execute("SELECT * FROM retailers").fetchall()
        nearby = [r for r in retailers if _haversine(w_lat, w_lon, r["latitude"], r["longitude"]) <= 10]
        total_demand = sum(r["demand"] for r in nearby)
        conn.close()
        result = {
            "warehouse": warehouse_name,
            "nearby_retailers": len(nearby),
            "total_demand": total_demand
        }
        nlg = generate_nlg(result, intent="calculate_demand")
        return {"result": result, "nlg": nlg}

    elif top_label == "what if":
        constraints = constraint_parser(user_input)
        from optimizer.solver import solve_routing
        result = solve_routing(constraints=constraints)
        conn.close()
        nlg = generate_nlg(result, intent="what_if")
        return {"result": result, "nlg": nlg}

    else:
        conn.close()
        nlg = "Sorry, I couldn't understand your request."
        return {"result": {}, "nlg": nlg}
# ===== Helpers =====
def _find_warehouse_in_text(user_input, conn):
    warehouses = conn.execute("SELECT name FROM warehouses").fetchall()
    user_input_lower = user_input.lower()
    for w in warehouses:
        name = w["name"].lower()
        if name in user_input_lower:
            return w["name"]
    return None

def _haversine(lat1, lon1, lat2, lon2):
    from math import radians, cos, sin, asin, sqrt
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c
