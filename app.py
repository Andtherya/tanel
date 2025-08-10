import os
from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime, timedelta
import uuid

base_path_raw = os.environ.get("BASE_PATH", "sub").strip("/")
BASE_PATH = "/" + base_path_raw

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
