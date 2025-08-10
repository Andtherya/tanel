from flask import Flask, render_template, request, jsonify
import json, os
from datetime import datetime

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/events", methods=["GET", "POST", "DELETE"])
def events_api():
    events = load_events()
    if request.method == "POST":
        data = request.json
        events.append(data)
        save_events(events)
        return jsonify({"status": "ok"})
    elif request.method == "DELETE":
        name = request.args.get("name")
        events = [e for e in events if e["name"] != name]
        save_events(events)
        return jsonify({"status": "ok"})
    else:
        today = datetime.now().date()
        for e in events:
            target_date = datetime.strptime(e["date"], "%Y-%m-%d").date()
            e["days_left"] = (target_date - today).days
        events.sort(key=lambda x: x["days_left"])
        return jsonify(events)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
