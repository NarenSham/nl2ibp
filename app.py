from flask import Flask, render_template, request, jsonify, session
from models import SessionLocal, Scenario, ScenarioOverride
from bot.parser import parse_query
from contextlib import contextmanager
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_super_secret_key"

# Context manager for SQLAlchemy session
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

# =====================================
# Startup: Print scenarios
# =====================================
with get_db() as db:
    scenarios = db.query(Scenario).all()
    for s in scenarios:
        print(f"[Startup] Scenario loaded: {s.name} ({s.type})")

# =====================================
# Routes
# =====================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_query = data.get("query", "")
    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    parsed = parse_query(user_query)
    nlg_text = parsed.get("nlg", "")
    if not isinstance(nlg_text, str):
        nlg_text = str(nlg_text)

    # Track scenario modifications in session
    if "modifications" in parsed and session.get("active_scenario_id") and session.get("scenario_mode") == "edit":
        if "scenario_changes" not in session:
            session["scenario_changes"] = []
        session["scenario_changes"].extend(parsed["modifications"])


    return jsonify({
        "response": parsed.get("result"),
        "nlg": nlg_text
    })


@app.route("/api/scenario/start", methods=["POST"])
def start_scenario():
    data = request.get_json() or {}
    scenario_type = data.get("type", "tpo")   # type from frontend
    scenario_name = data.get("name", "New Scenario")

    with get_db() as db:
        new_scenario = Scenario(
            name=scenario_name,
            description="User-created scenario",
            type=scenario_type,
            created_at=datetime.utcnow()
        )
        db.add(new_scenario)
        db.flush()
        scenario_id = new_scenario.scenario_id   # correct ID field

    session["active_scenario_id"] = scenario_id
    session["scenario_changes"] = []

    return jsonify({"scenario_id": scenario_id, "status": "started"})


@app.route("/api/scenario/load", methods=["POST"])
def load_scenario():
    data = request.get_json()
    scenario_id = data.get("scenario_id")

    if not scenario_id:
        return jsonify({"error": "scenario_id required"}), 400

    with get_db() as db:
        # Load scenario for **view-only analysis**, not edit
        overrides_json = hydrate_scenario_in_session(db, scenario_id, edit_mode=False)
        scenario = db.query(Scenario).filter_by(scenario_id=scenario_id).first()
        scenario_name = scenario.name if scenario else "Unknown"

    return jsonify({
        "status": "loaded",
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "overrides": overrides_json
    })



@app.route("/api/scenario/list")
def list_scenarios():
    with get_db() as db:
        scenarios = db.query(Scenario).distinct(Scenario.scenario_id).all()
        # OR: remove duplicates manually
        seen = set()
        result = []
        for s in scenarios:
            if s.scenario_id in seen:
                continue
            seen.add(s.scenario_id)
            result.append({"id": s.scenario_id, "name": s.name, "type": s.type})
    return jsonify({"scenarios": result})


@app.route("/api/scenario/save", methods=["POST"])
def save_scenario():
    data = request.get_json()
    scenario_id = data.get("scenario_id")
    scenario_name = data.get("scenario_name")
    scenario_type = data.get("scenario_type", "tpo")
    changes = data.get("changes", [])

    if not changes and not scenario_name:
        return jsonify({"error": "No changes or scenario name to save"}), 400

    with get_db() as db:
        # ---------- CREATE NEW SCENARIO ----------
        if not scenario_id:
            if not scenario_name:
                return jsonify({"error": "Scenario name required for new scenario"}), 400

            # 🔑 NEW: check if a scenario with the same name+type already exists
            existing = db.query(Scenario).filter_by(name=scenario_name, type=scenario_type).first()
            if existing:
                # treat it as update instead of creating duplicate
                scenario_id = existing.scenario_id
                db.query(ScenarioOverride).filter_by(scenario_id=scenario_id).delete()
                scenario = existing
            else:
                new_scenario = Scenario(
                    name=scenario_name,
                    description="User-created scenario",
                    type=scenario_type,
                    created_at=datetime.utcnow()
                )
                db.add(new_scenario)
                db.flush()
                scenario_id = new_scenario.scenario_id
                scenario = new_scenario

        # ---------- UPDATE EXISTING SCENARIO ----------
        else:
            scenario = db.query(Scenario).filter_by(scenario_id=scenario_id).first()
            if not scenario:
                return jsonify({"error": f"Scenario {scenario_id} not found"}), 404
            if scenario_name:
                scenario.name = scenario_name
            db.query(ScenarioOverride).filter_by(scenario_id=scenario_id).delete()

        # ---------- INSERT NEW OVERRIDES ----------
        for c in changes:
            override = ScenarioOverride(
                scenario_id=scenario_id,
                table_name=c.get("table"),
                row_id=c.get("row_id"),
                column_name=c.get("column"),
                override_value=str(c.get("new_value"))
            )
            db.add(override)

        saved_name = scenario.name
        saved_id = scenario_id

        db.commit()

        # ---------- HYDRATE SESSION ----------
        overrides_json = hydrate_scenario_in_session(db, scenario_id)

        # reset scenario mode after save
        session.pop("active_scenario_id", None)
        session.pop("scenario_changes", None)
        session.pop("scenario_mode", None)

    return jsonify({
        "status": "saved",
        "scenario_id": saved_id,
        "scenario_name": saved_name,
        "overrides": overrides_json
    })


#   Refactor your load logic into a helper function, then call it both from save_scenario and load_scenario.

def hydrate_scenario_in_session(db, scenario_id, edit_mode=False):
    overrides = db.query(ScenarioOverride).filter_by(scenario_id=scenario_id).all()
    overrides_json = [
        {
            "id": o.id,
            "table_name": o.table_name,
            "row_id": o.row_id,
            "column_name": o.column_name,
            "override_value": o.override_value
        }
        for o in overrides
    ]

    if edit_mode:
        # Scenario user can edit
        session["active_scenario_id"] = scenario_id
        session["scenario_changes"] = overrides_json
    else:
        # Scenario loaded for view-only analysis
        session["loaded_scenario_id"] = scenario_id

    return overrides_json





if __name__ == "__main__":
    app.run(debug=True)
