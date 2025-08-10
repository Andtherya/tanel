from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
import json, os
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
DATA_FILE = "/app/events.json"
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD", "123456")

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

def load_events():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_events(events):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def check_auth():
    return request.cookies.get("access_granted") == "true"

@app.before_request
def require_password():
    if request.path in ["/login", "/favicon.ico"] or request.path.startswith("/static/"):
        return None
    if not check_auth():
        return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == ACCESS_PASSWORD:
            resp = make_response(redirect(url_for("index")))
            resp.set_cookie("access_granted", "true", max_age=7*24*3600, httponly=True)
            return resp
        else:
            error = "密码错误"
    return render_template("login.html", error=error)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/events", methods=["GET", "POST"])
def events_api():
    if not check_auth():
        return jsonify({"error":"Unauthorized"}), 401

    if request.method == "POST":
        data = request.json or {}
        name = data.get("name", "").strip()
        duration_seconds = data.get("duration_seconds")
        if not name:
            return jsonify({"error": "name required"}), 400
        if duration_seconds is None:
            return jsonify({"error": "duration_seconds required"}), 400
        try:
            ds = int(duration_seconds)
            if ds <= 0:
                return jsonify({"error": "duration_seconds must > 0"}), 400
        except:
            return jsonify({"error": "invalid duration_seconds"}), 400

        now = datetime.now()
        target = now + timedelta(seconds=ds)

        ev = {
            "id": str(uuid.uuid4()),
            "name": name,
            "target": target.strftime("%Y-%m-%dT%H:%M:%S"),
            "duration_seconds": ds
        }
        events = load_events()
        events.append(ev)
        save_events(events)
        return jsonify({"status": "ok", "event": ev})

    else:
        events = load_events()
        now = datetime.now()
        out = []
        for e in events:
            try:
                target = datetime.strptime(e["target"], "%Y-%m-%dT%H:%M:%S")
            except:
                target = datetime.strptime(e["target"], "%Y-%m-%d")
            seconds_left = int((target - now).total_seconds())
            out.append({
                "id": e.get("id"),
                "name": e.get("name"),
                "target": e.get("target"),
                "seconds_left": seconds_left,
                "duration_seconds": e.get("duration_seconds", 0)
            })
        out.sort(key=lambda x: x["seconds_left"])
        return jsonify(out)

@app.route("/api/events/<eid>", methods=["DELETE"])
def delete_event(eid):
    if not check_auth():
        return jsonify({"error":"Unauthorized"}), 401
    events = load_events()
    new = [e for e in events if e.get("id") != eid]
    if len(new) == len(events):
        return jsonify({"error": "not found"}), 404
    save_events(new)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
