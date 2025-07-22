from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import date, datetime
import os

app = Flask(__name__)

def init_db():
    with sqlite3.connect("workdays.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workdays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                work_date TEXT NOT NULL,
                UNIQUE(username, work_date)
            )
        """)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/log", methods=["POST"])
def log_today():
    data = request.get_json()
    username = data.get('username') if data else None
    
    if not username:
        return jsonify({"status": "error", "message": "Username is required"}), 400
    
    today = date.today().isoformat()
    try:
        with sqlite3.connect("workdays.db") as conn:
            conn.execute("INSERT OR IGNORE INTO workdays (username, work_date) VALUES (?, ?)", (username, today))
        return jsonify({"status": "success", "date": today})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/log/<date_str>", methods=["POST"])
def log_specific_date(date_str):
    data = request.get_json()
    username = data.get('username') if data else None
    
    if not username:
        return jsonify({"status": "error", "message": "Username is required"}), 400
    
    try:
        # Validate date format
        datetime.strptime(date_str, '%Y-%m-%d')
        
        with sqlite3.connect("workdays.db") as conn:
            conn.execute("INSERT OR IGNORE INTO workdays (username, work_date) VALUES (?, ?)", (username, date_str))
        return jsonify({"status": "success", "date": date_str})
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/remove/<date_str>", methods=["DELETE"])
def remove_workday(date_str):
    data = request.get_json()
    username = data.get('username') if data else None
    
    if not username:
        return jsonify({"status": "error", "message": "Username is required"}), 400
    
    try:
        with sqlite3.connect("workdays.db") as conn:
            cursor = conn.execute("DELETE FROM workdays WHERE username = ? AND work_date = ?", (username, date_str))
            if cursor.rowcount > 0:
                return jsonify({"status": "success", "message": f"Removed workday for {date_str}"})
            else:
                return jsonify({"status": "error", "message": "Date not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/days")
def get_days():
    username = request.args.get('username')
    
    if not username:
        return jsonify({"status": "error", "message": "Username is required"}), 400
    
    with sqlite3.connect("workdays.db") as conn:
        rows = conn.execute("SELECT work_date FROM workdays WHERE username = ?", (username,)).fetchall()
        days = [r[0] for r in rows]
    return jsonify(days)

@app.route("/api/users")
def get_users():
    with sqlite3.connect("workdays.db") as conn:
        rows = conn.execute("SELECT DISTINCT username FROM workdays ORDER BY username").fetchall()
        users = [r[0] for r in rows]
    return jsonify(users)

if __name__ == "__main__":
    init_db()
    # Use environment variable for port (Render requirement)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
