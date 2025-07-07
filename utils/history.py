import json
import os
from datetime import datetime

HISTORY_FILE = "match_history.json"

def save_match(resume_text, jd_text, feedback):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resume_excerpt": resume_text[:300],
        "jd_excerpt": jd_text[:300],
        "feedback": feedback
    }

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    history.insert(0, entry)  # add newest match to top

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def get_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []
