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

    response = parse_query(user_query)
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True)
