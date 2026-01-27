import json
import os
from pathlib import Path
from datetime import datetime

# Define data path relative to this tool file
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_FILE = DATA_DIR / "time_log.json"

def log_activity(activity_name: str, duration_minutes: int) -> str:
    """
    Log a completed work activity and its duration.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
            
    entry = {
        "activity": activity_name,
        "duration_minutes": duration_minutes,
        "timestamp": datetime.now().isoformat()
    }
    logs.append(entry)
    
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4)
        
    return f"Logged: '{activity_name}' for {duration_minutes} minutes."
