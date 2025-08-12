from flask import Flask, render_template, request, jsonify, session
import sqlite3
from bot.parser import parse_query

app = Flask(__name__)
app.secret_key = "your_super_secret_key"
DB_PATH = "db/optiguide.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

    # If scenario active and parse_query tells us a change happened
    if "modifications" in parsed and session.get("active_scenario_id"):
        if "scenario_changes" not in session:
            session["scenario_changes"] = []
        session["scenario_changes"].extend(parsed["modifications"])

    return jsonify({
        "response": parsed.get("result"),
        "nlg": nlg_text
    })

@app.route("/api/scenario/start", methods=["POST"])
def start_scenario():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO scenario (name, description, created_at) VALUES (?, ?, datetime('now'))",
        ("New Scenario", "User-created scenario")
    )
    scenario_id = cursor.lastrowid
    conn.commit()
    conn.close()

    session["active_scenario_id"] = scenario_id
    session["scenario_changes"] = []
    return jsonify({"scenario_id": scenario_id, "status": "started"})


@app.route("/api/scenario/load", methods=["POST"])
def load_scenario():
    data = request.get_json()
    scenario_id = data.get("scenario_id")

    if not scenario_id:
        return jsonify({"error": "scenario_id required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM scenario_overrides WHERE scenario_id = ?", (scenario_id,))
    overrides = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Here you’d apply the overrides to your baseline data in memory or in query layer
    # For now, we just return them
    session["active_scenario_id"] = scenario_id
    session["scenario_changes"] = overrides

    return jsonify({
        "status": "loaded",
        "scenario_id": scenario_id,
        "overrides": overrides
    })
@app.route("/api/scenario/list")
def list_scenarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM scenario ORDER BY created_at DESC")
    scenarios = cursor.fetchall()
    conn.close()
    return jsonify({"scenarios": [{"id": s["id"], "name": s["name"]} for s in scenarios]})

@app.route("/api/scenario/save", methods=["POST"])
def save_scenario():
    data = request.get_json()
    scenario_id = data.get("scenario_id")
    scenario_name = data.get("scenario_name")
    changes = data.get("changes", [])

    if not changes:
        return jsonify({"error": "No changes to save"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # If no scenario_id, create new scenario
        if not scenario_id:
            if not scenario_name:
                return jsonify({"error": "Scenario name required for new scenario"}), 400
            cursor.execute(
                "INSERT INTO scenario (name, description, created_at) VALUES (?, ?, datetime('now'))",
                (scenario_name, "User-created scenario"),
            )
            scenario_id = cursor.lastrowid
        else:
            # Overwrite scenario name if given
            if scenario_name:
                cursor.execute("UPDATE scenario SET name = ? WHERE id = ?", (scenario_name, scenario_id))
            # Delete old overrides for this scenario to overwrite
            cursor.execute("DELETE FROM scenario_overrides WHERE scenario_id = ?", (scenario_id,))

        # Insert new overrides
        for c in changes:
            cursor.execute(
                """
                INSERT INTO scenario_overrides
                (scenario_id, table_name, row_id, column_name, override_value)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    scenario_id,
                    c.get("table"),
                    c.get("row_id"),
                    c.get("column"),
                    str(c.get("new_value")),
                ),
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Failed to save scenario: {e}"}), 500
    finally:
        conn.close()

    return jsonify({"status": "saved", "scenario_id": scenario_id})


if __name__ == "__main__":
    app.run(debug=True)
