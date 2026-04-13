"""
Memory tools — persistent key-value store, task tracker, and context management.
"""

import json
import os
import uuid
import datetime
from friday.config import config

# Default memory state
_STATE = {
    "memories": {},
    "tasks": {}
}

# The target file for saving data
_MEM_FILE = 'friday_memory.json'

def load_memory():
    global _STATE
    path = config.MEMORY_FILE or _MEM_FILE
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _STATE["memories"] = data.get("memories", {})
                _STATE["tasks"] = data.get("tasks", {})
        except Exception:
            pass

def save_memory():
    path = config.MEMORY_FILE or _MEM_FILE
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(_STATE, f, indent=2)
    except Exception:
        pass

# Initialize on import
load_memory()
_START_TIME = datetime.datetime.now()

def register(mcp):

    @mcp.tool()
    def remember(key: str, value: str, tags: str = "") -> str:
        """Stores a key-value memory permanently."""
        _STATE["memories"][key] = {
            "value": value,
            "tags": tags,
            "updated": datetime.datetime.now().isoformat()
        }
        save_memory()
        return f"Committed to memory under key '{key}'."

    @mcp.tool()
    def recall(key: str) -> str:
        """Recalls a stored value by key."""
        if key in _STATE["memories"]:
            return f"Value for '{key}': {_STATE['memories'][key]['value']}"
        return f"I have no memory of '{key}'."

    @mcp.tool()
    def forget(key: str) -> str:
        """Removes a key from memory."""
        if key in _STATE["memories"]:
            del _STATE["memories"][key]
            save_memory()
            return f"Wiped '{key}' from memory banks."
        return f"'{key}' wasn't in memory anyway."

    @mcp.tool()
    def add_task(title: str, priority: str = "normal") -> str:
        """Adds a task to the lab queue."""
        uid = str(uuid.uuid4())[:8]
        _STATE["tasks"][uid] = {
            "title": title,
            "priority": priority,
            "status": "pending",
            "created": datetime.datetime.now().isoformat()
        }
        save_memory()
        return f"Task added with ID {uid}."

    @mcp.tool()
    def complete_task(task_id: str) -> str:
        """Marks a task as completed."""
        if task_id in _STATE["tasks"]:
            _STATE["tasks"][task_id]["status"] = "completed"
            save_memory()
            return f"Task {task_id} marked as completed."
        return f"Could not find task {task_id}."

    @mcp.tool()
    def list_tasks() -> str:
        """Lists all pending tasks."""
        pending = {k: v for k, v in _STATE["tasks"].items() if v["status"] == "pending"}
        if not pending:
            return "No pending tasks."
        report = ["## TASK QUEUE ##"]
        for k, v in pending.items():
            report.append(f"[{k}] {v['priority'].upper():6} : {v['title']}")
        return "\n".join(report)

    @mcp.tool()
    def clear_tasks() -> str:
        """Clears all completed tasks from the queue."""
        before = len(_STATE["tasks"])
        _STATE["tasks"] = {k: v for k, v in _STATE["tasks"].items() if v["status"] != "completed"}
        cleared = before - len(_STATE["tasks"])
        save_memory()
        return f"Cleared {cleared} completed tasks from the queue."

    @mcp.tool()
    def session_summary() -> str:
        """Returns a snapshot of current system uptime, all memories, and pending tasks."""
        uptime = datetime.datetime.now() - _START_TIME
        report = [f"## SESSION REPORT ##", f"Uptime: {str(uptime).split('.')[0]}"]
        
        report.append("\n-- MEMORIES --")
        if _STATE["memories"]:
            for k, v in _STATE["memories"].items():
                report.append(f"  {k}: {v['value']}")
        else:
            report.append("  (Memory banks empty)")
            
        report.append("\n-- PENDING TASKS --")
        pending = {k: v for k, v in _STATE["tasks"].items() if v["status"] == "pending"}
        if pending:
            for k, v in pending.items():
                report.append(f"  [{k}] {v['title']} (Priority: {v['priority']})")
        else:
            report.append("  (Task queue empty)")
            
        return "\n".join(report)
