import flask
from flask import Flask, render_template, request, jsonify
import sqlite3
from bot.parser import parse_query

app = Flask(__name__)
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


if __name__ == "__main__":
    app.run(debug=True)
