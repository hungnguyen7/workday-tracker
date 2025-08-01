from flask import Flask, request, jsonify, render_template
import psycopg2
import psycopg2.extras
from datetime import date, datetime
import os
from urllib.parse import urlparse

app = Flask(__name__)

# Database configuration
def get_db_connection():
    """Get database connection from environment variable or fallback to local"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Parse the DATABASE_URL for Render PostgreSQL
        url = urlparse(database_url)
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],  # Remove leading slash
            user=url.username,
            password=url.password,
            sslmode='require'  # Required for cloud databases
        )
    else:
        # Local development fallback
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432'),
            database=os.environ.get('DB_NAME', 'workdays'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', '')
        )
    
    return conn

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workdays (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    work_date DATE NOT NULL,
                    UNIQUE(username, work_date)
                )
            """)
            conn.commit()

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
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO workdays (username, work_date) VALUES (%s, %s) ON CONFLICT (username, work_date) DO NOTHING", (username, today))
                conn.commit()
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
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO workdays (username, work_date) VALUES (%s, %s) ON CONFLICT (username, work_date) DO NOTHING", (username, date_str))
                conn.commit()
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
        # Validate date format
        datetime.strptime(date_str, '%Y-%m-%d')
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM workdays WHERE username = %s AND work_date = %s", (username, date_str))
                if cur.rowcount > 0:
                    conn.commit()
                    return jsonify({"status": "success", "message": f"Removed workday for {date_str}"})
                else:
                    return jsonify({"status": "error", "message": "Date not found"}), 404
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/days")
def get_days():
    username = request.args.get('username')
    
    if not username:
        return jsonify({"status": "error", "message": "Username is required"}), 400
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT work_date FROM workdays WHERE username = %s ORDER BY work_date", (username,))
                rows = cur.fetchall()
                # Convert date objects to ISO format strings
                days = [row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]) for row in rows]
        return jsonify(days)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/users")
def get_users():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT username FROM workdays ORDER BY username")
                rows = cur.fetchall()
                users = [row[0] for row in rows]
        return jsonify(users)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    init_db()
    # Use environment variable for port (Render requirement)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
