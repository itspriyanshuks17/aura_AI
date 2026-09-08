"""
tools/memory_tools.py
Small persistent key-value store so the agent can remember things like
"my backend container is called myapp-api" across sessions, instead of
you having to repeat yourself every time.

Stored as plain JSON at ~/.aura/memory.json (configurable).
"""

from __future__ import annotations

import json
import os

from aura.config import settings
from aura.tools.registry import Risk, tool


def _load() -> dict:
    if not os.path.exists(settings.memory_path):
        return {}
    try:
        with open(settings.memory_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(settings.memory_path), exist_ok=True)
    with open(settings.memory_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@tool(
    description=(
        "Remember a fact for future sessions, e.g. remember(key='backend_container', "
        "value='myapp-api') so the user can later say 'restart my backend' instead of "
        "naming the container every time."
    ),
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Short identifier for this fact."},
            "value": {"type": "string", "description": "The value to remember."},
        },
        "required": ["key", "value"],
    },
    risk=Risk.SAFE,
)
def memory_remember(key: str, value: str) -> dict:
    data = _load()
    data[key] = value
    _save(data)
    return {"result": f"Remembered {key} = {value}"}


@tool(
    description="Recall a previously remembered fact by key.",
    parameters={
        "type": "object",
        "properties": {"key": {"type": "string", "description": "The key to look up."}},
        "required": ["key"],
    },
    risk=Risk.SAFE,
)
def memory_recall(key: str) -> dict:
    data = _load()
    if key not in data:
        return {"error": f"No memory found for '{key}'."}
    return {key: data[key]}


@tool(
    description="List every fact currently remembered.",
    parameters={"type": "object", "properties": {}, "required": []},
    risk=Risk.SAFE,
)
def memory_list() -> dict:
    return _load()


@tool(
    description="Forget a previously remembered fact by key.",
    parameters={
        "type": "object",
        "properties": {"key": {"type": "string", "description": "The key to remove."}},
        "required": ["key"],
    },
    risk=Risk.CONFIRM,
)
def memory_forget(key: str) -> dict:
    data = _load()
    if key in data:
        del data[key]
        _save(data)
        return {"result": f"Forgot '{key}'."}
    return {"error": f"No memory found for '{key}'."}
