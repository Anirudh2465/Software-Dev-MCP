import os
from pathlib import Path
from datetime import datetime

# Define data path relative to this tool file
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
JOURNAL_FILE = DATA_DIR / "journal.md"

def write_journal_entry(text: str) -> str:
    """
    Append a new entry to the daily journal.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n## {timestamp}\n{text}\n"
    
    try:
        with open(JOURNAL_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        return f"Journal entry saved for {timestamp}."
    except Exception as e:
        return f"Error saving journal entry: {str(e)}"
