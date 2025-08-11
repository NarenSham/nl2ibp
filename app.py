import flask
from flask import Flask, render_template, request, jsonify, session
import sqlite3
from bot.parser import parse_query

app = Flask(__name__)
app.secret_key = "your_super_secret_key"  # Replace with a secure random key for production
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

    parsed = parse_query(user_query)  # dict with keys 'result' and 'nlg'

    nlg_text = parsed.get("nlg", "")
    if not isinstance(nlg_text, str):
        nlg_text = str(nlg_text)

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
    return jsonify({"scenario_id": scenario_id, "status": "started"})


@app.route("/api/scenario/save", methods=["POST"])
def save_scenario():
    data = request.get_json()
    scenario_id = data.get("scenario_id")
    overrides = data.get("overrides", [])  # Expecting a list of override dicts
    
    if not scenario_id or not overrides:
        return jsonify({"error": "scenario_id and overrides required"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for o in overrides:
            cursor.execute(
                """
                INSERT INTO scenario_overrides
                (scenario_id, table_name, row_id, column_name, override_value)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    scenario_id,
                    o.get("table_name"),
                    o.get("row_id"),
                    o.get("column_name"),
                    str(o.get("override_value")),
                ),
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Failed to save scenario: {e}"}), 500
    finally:
        conn.close()
    
    return jsonify({"status": "success", "message": "Scenario overrides saved"})



if __name__ == "__main__":
    app.run(debug=True)
