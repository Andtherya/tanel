import os
from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime, timedelta
import uuid

BASE_PATH = os.environ.get("BASE_PATH", "/sub").rstrip("/")

app = Flask(__name__)
DATA_FILE = "/app/events.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

def load_events():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_events(events):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def parse_datetime_local(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    except:
        try:
            return datetime.strptime(s, "%Y-%m-%dT%H:%M")
        except:
            return None

@app.route("/")
def home():
    return "<h1>Hello World</h1>"

@app.route(f"{BASE_PATH}")
def index():
    return render_template("index.html", base_path=BASE_PATH)

@app.route(f"{BASE_PATH}/api/events", methods=["GET", "POST"])
def events_api():
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
            dt = parse_datetime_local(date_str)
            if not dt:
                return jsonify({"error": "invalid date format"}), 400
            target = dt
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

@app.route(f"{BASE_PATH}/api/events/<eid>", methods=["DELETE"])
def delete_event(eid):
    events = load_events()
    new = [e for e in events if e.get("id") != eid]
    if len(new) == len(events):
        return jsonify({"error": "not found"}), 404
    save_events(new)
    return jsonify({"status": "ok"})
