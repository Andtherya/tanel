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
    # 判断请求 Cookie 是否有授权
    return request.cookies.get("access_granted") == "true"

@app.before_request
def require_password():
    if request.path in ["/login", "/favicon.ico"] or request.path.startswith("/static/"):
        return None  # 登录页和静态资源无需密码
    if not check_auth():
        return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == ACCESS_PASSWORD:
            resp = make_response(redirect(url_for("index")))
            # 设置 cookie 7 天有效
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
        if not name:
            return jsonify({"error": "name required"}), 400

        date_str = data.get("date")
        duration_seconds = data.get("duration_seconds")

        now = datetime.now()
        target = None

        if date_str:
            try:
                target = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
            except:
                try:
                    target = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
                except:
                    return jsonify({"error": "invalid date format"}), 400
        elif duration_seconds is not None:
            try:
                ds = int(duration_seconds)
            except:
                return jsonify({"error": "invalid duration_seconds"}), 400
            target = now + timedelta(seconds=ds)
        else:
            return jsonify({"error": "either date or duration_seconds required"}), 400

        ev = {
            "id": str(uuid.uuid4()),
            "name": name,
            "target": target.strftime("%Y-%m-%dT%H:%M:%S")
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
                "seconds_left": seconds_left
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
