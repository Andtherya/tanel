from flask import Flask, render_template, request, jsonify
import json, os
from datetime import datetime, timedelta, timezone
import uuid

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
    # s from browser datetime-local: "YYYY-MM-DDTHH:MM" or "YYYY-MM-DDTHH:MM:SS"
    if not s:
        return None
    try:
        # try with seconds
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    except:
        try:
            return datetime.strptime(s, "%Y-%m-%dT%H:%M")
        except:
            return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/events", methods=["GET", "POST"])
def events_api():
    if request.method == "POST":
        data = request.json or {}
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"error": "name required"}), 400

        # prefer explicit date if given
        date_str = data.get("date")  # from datetime-local (e.g. "2025-08-10T09:12")
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
            # store ISO-local (no timezone) for simplicity
            "target": target.strftime("%Y-%m-%dT%H:%M:%S")
        }
        events = load_events()
        events.append(ev)
        save_events(events)
        return jsonify({"status": "ok", "event": ev})

    else:  # GET
        events = load_events()
        now = datetime.now()
        out = []
        for e in events:
            try:
                target = datetime.strptime(e["target"], "%Y-%m-%dT%H:%M:%S")
            except:
                # fallback: try date-only
                target = datetime.strptime(e["target"], "%Y-%m-%d")
            seconds_left = int((target - now).total_seconds())
            out.append({
                "id": e.get("id"),
                "name": e.get("name"),
                "target": e.get("target"),
                "seconds_left": seconds_left
            })
        # sort by seconds_left ascending
        out.sort(key=lambda x: x["seconds_left"])
        return jsonify(out)

@app.route("/api/events/<eid>", methods=["DELETE"])
def delete_event(eid):
    events = load_events()
    new = [e for e in events if e.get("id") != eid]
    if len(new) == len(events):
        return jsonify({"error": "not found"}), 404
    save_events(new)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    # only used for local debugging, in container we'll use gunicorn
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
