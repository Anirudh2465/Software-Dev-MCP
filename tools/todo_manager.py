import json
import os
from pathlib import Path
from datetime import datetime

# Define data path relative to this tool file
# tools/ -> root/ -> data/
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TODO_FILE = DATA_DIR / "todo.json"

def _load_todos():
    if not os.path.exists(TODO_FILE):
        return []
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_todos(todos):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=4)

def add_task(task: str) -> str:
    """
    Add a new task to the todo list.
    """
    todos = _load_todos()
    new_id = len(todos) + 1
    new_task = {
        "id": new_id,
        "task": task,
        "completed": False,
        "created_at": datetime.now().isoformat()
    }
    todos.append(new_task)
    _save_todos(todos)
    return f"Task added with ID {new_id}: '{task}'"

def list_tasks() -> str:
    """
    List all pending tasks.
    """
    todos = _load_todos()
    pending = [t for t in todos if not t["completed"]]
    if not pending:
        return "No pending tasks."
    
    output = "Pending Tasks:\n"
    for t in pending:
        output += f"[{t['id']}] {t['task']}\n"
    return output

def complete_task(task_id: int) -> str:
    """
    Mark a task as complete by its ID.
    """
    todos = _load_todos()
    for t in todos:
        if t["id"] == task_id:
            if t["completed"]:
                return f"Task {task_id} is already completed."
            t["completed"] = True
            t["completed_at"] = datetime.now().isoformat()
            _save_todos(todos)
            return f"Task {task_id} marked as complete."
    return f"Task with ID {task_id} not found."
