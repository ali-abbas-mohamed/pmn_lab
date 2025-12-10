from flask import Flask, request, render_template_string, Response, jsonify, redirect, url_for
import re, requests, os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Database connection (PostgreSQL via env variable, fallback to SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///logs.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Authentication setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# LogEntry model
class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    level = db.Column(db.String(20))
    user = db.Column(db.String(50))
    message = db.Column(db.Text)
    role = db.Column(db.String(50))

# Remote log file URL (set via environment variable)
REMOTE_LOG_URL = os.getenv("REMOTE_LOG_URL", "https://example.com/sample.log")

# Regex pattern for log format
log_pattern = re.compile(
    r'^(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(?P<level>\w+)\]\s+\[(?P<user>[^\]]+)\]\s+(?P<message>.+?)(?:\s+\(Role:\s+(?P<role>[^\)]+)\))?$'
)

# --- Utility: fetch and store logs dynamically ---
def fetch_and_store_logs():
    try:
        response = requests.get(REMOTE_LOG_URL, timeout=10)
        response.raise_for_status()
        log_lines = response.text.splitlines()

        for line in log_lines:
            match = log_pattern.match(line.strip())
            if match:
                data = match.groupdict()
                ts = datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S")

                # Avoid duplicates
                exists = LogEntry.query.filter_by(timestamp=ts, user=data['user'], message=data['message']).first()
                if not exists:
                    entry = LogEntry(
                        timestamp=ts,
                        level=data['level'],
                        user=data['user'],
                        message=data['message'],
                        role=data.get('role')
                    )
                    db.session.add(entry)
        db.session.commit()
    except Exception as e:
        print(f"Error fetching logs: {e}")
        db.session.rollback()

# --- Routes ---
@app.route("/")
@login_required
def index():
    # Always refresh logs dynamically
    fetch_and_store_logs()

    # Filters
    user_filter = request.args.get("user")
    date_filter = request.args.get("date")

    query = LogEntry.query
    if user_filter:
        query = query.filter(LogEntry.user == user_filter)
    if date_filter:
        try:
            date_obj = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter(db.func.date(LogEntry.timestamp) == date_obj)
        except ValueError:
            pass

    logs = query.order_by(LogEntry.timestamp.desc()).all()

    template = """
    <html>
    <head><title>Dynamic Log Viewer</title></head>
    <body>
        <h1>Logs (Fetched from Remote HTTPS)</h1>
        <table border="1">
            <tr><th>Timestamp</th><th>Level</th><th>User</th><th>Message</th><th>Role</th></tr>
            {% for log in logs %}
            <tr>
                <td>{{ log.timestamp }}</td>
                <td>{{ log.level }}</td>
                <td>{{ log.user }}</td>
                <td>{{ log.message }}</td>
                <td>{{ log.role if log.role else "N/A" }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(template, logs=logs)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "password":
            login_user(User(id=1))
            return redirect(url_for("index"))
        return "Invalid credentials", 401
    return """
    <form method="post">
        <input name="username" placeholder="Username">
        <input name="password" type="password" placeholder="Password">
        <button type="submit">Login</button>
    </form>
    """

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)