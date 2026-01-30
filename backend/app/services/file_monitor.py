
import os
import datetime
from pymongo import MongoClient
import json
from pathlib import Path

# Load env (though usually loaded by main)
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

class FileMonitorService:
    def __init__(self):
        self.client = None
        self.collection = None
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client["jarvis_db"]
            self.collection = self.db["monitored_directories"]
            print("Connected to MongoDB (FileMonitor)")
        except Exception as e:
            print(f"Error connecting to MongoDB (FileMonitor): {e}")

    def add_directory(self, path: str):
        if self.collection is None:
            return {"status": "error", "message": "DB connection failed"}
        
        # Normalize path
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
             return {"status": "error", "message": "Directory does not exist"}

        if self.collection.find_one({"path": abs_path}):
             return {"status": "error", "message": "Directory already monitored"}

        doc = {
            "path": abs_path,
            "added_at": datetime.datetime.now().isoformat(),
        }
        self.collection.insert_one(doc)
        return {"status": "success", "message": f"Added {abs_path}", "path": abs_path}

    def get_directories(self):
        if self.collection is None: return []
        return list(self.collection.find({}, {"_id": 0}))

    def remove_directory(self, path: str):
        if self.collection is None: return False
        res = self.collection.delete_one({"path": path})
        return res.deleted_count > 0

    def list_path_contents(self, path: str):
        """
        Returns immediate children of the path.
        Checks if the path is within a monitored directory (optional but recommended).
        """
        if not os.path.exists(path):
            return None
            
        try:
            items = []
            with os.scandir(path) as it:
                for entry in it:
                    # Skip hidden/system files
                    if entry.name.startswith('.') or entry.name in {'__pycache__', 'node_modules', 'venv', 'dist', 'build'}:
                        continue
                        
                    items.append({
                        "name": entry.name,
                        "path": entry.path,
                        "type": "directory" if entry.is_dir() else "file",
                        "size": entry.stat().st_size if entry.is_file() else 0
                    })
            # Sort: Directories first, then files
            items.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
            return items
        except Exception as e:
            print(f"Error listing {path}: {e}")
            return []

    def get_monitored_context(self):
        """
        Returns a summary of monitored roots for Context Injection.
        """
        if self.collection is None: return ""
        
        text = "Monitored Directories (Access Allowed):\n"
        dirs = self.get_directories()
        for d in dirs:
            text += f"- {d['path']}\n"
        return text
