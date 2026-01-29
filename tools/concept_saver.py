import json
import os
from pathlib import Path

# Define data path relative to this tool file
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
GLOSSARY_FILE = DATA_DIR / "glossary.json"

def save_concept(term: str, definition: str) -> str:
    """
    Save a new concept and its definition to your personal glossary.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    glossary = {}
    if os.path.exists(GLOSSARY_FILE):
        try:
            with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
                glossary = json.load(f)
        except Exception:
            glossary = {}
            
    glossary[term] = definition
    
    with open(GLOSSARY_FILE, "w", encoding="utf-8") as f:
        json.dump(glossary, f, indent=4)
        
    return f"Concept saved: '{term}'."
