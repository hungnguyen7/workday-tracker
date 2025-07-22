from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import date, datetime

app = Flask(__name__)

def init_db():
    with sqlite3.connect("workdays.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workdays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_date TEXT UNIQUE
            )
        """)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/log", methods=["POST"])
def log_today():
    today = date.today().isoformat()
    try:
        with sqlite3.connect("workdays.db") as conn:
            conn.execute("INSERT OR IGNORE INTO workdays (work_date) VALUES (?)", (today,))
        return jsonify({"status": "success", "date": today})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/log/<date_str>", methods=["POST"])
def log_specific_date(date_str):
    try:
        # Validate date format
        datetime.strptime(date_str, '%Y-%m-%d')
        
        with sqlite3.connect("workdays.db") as conn:
            conn.execute("INSERT OR IGNORE INTO workdays (work_date) VALUES (?)", (date_str,))
        return jsonify({"status": "success", "date": date_str})
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/remove/<date_str>", methods=["DELETE"])
def remove_workday(date_str):
    try:
        with sqlite3.connect("workdays.db") as conn:
            cursor = conn.execute("DELETE FROM workdays WHERE work_date = ?", (date_str,))
            if cursor.rowcount > 0:
                return jsonify({"status": "success", "message": f"Removed workday for {date_str}"})
            else:
                return jsonify({"status": "error", "message": "Date not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/days")
def get_days():
    with sqlite3.connect("workdays.db") as conn:
        rows = conn.execute("SELECT work_date FROM workdays").fetchall()
        days = [r[0] for r in rows]
    return jsonify(days)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
