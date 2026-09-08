"""
tools/registry.py

A tiny, dependency-free tool registry.

Design principle (see the architecture notes this project is based on):
"Don't let the AI directly execute arbitrary commands. Give it controlled,
named tools instead." Every tool declares:
  - a JSON schema for its parameters (what the LLM is allowed to pass)
  - a risk level, used by security/permissions.py to decide whether to
    execute automatically, ask for a y/N confirmation, or demand an
    exact typed confirmation phrase.

Usage:

    from tools.registry import tool, Risk

    @tool(
        description="Get current RAM usage.",
        parameters={"type": "object", "properties": {}, "required": []},
        risk=Risk.SAFE,
    )
    def get_ram_status():
        ...
"""

from __future__ import annotations

import enum
import functools
from dataclasses import dataclass, field
from typing import Any, Callable


class Risk(str, enum.Enum):
    SAFE = "SAFE"            # read-only, executes automatically
    CONFIRM = "CONFIRM"      # mutating but reversible-ish, ask y/N
    DANGEROUS = "DANGEROUS"  # destructive, require typed confirmation phrase


@dataclass
class RegisteredTool:
    name: str
    description: str
    parameters: dict
    risk: Risk
    func: Callable[..., Any]

    def to_openai_schema(self) -> dict:
        """Render as an OpenAI-style function-calling tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolRegistry:
    _tools: dict = field(default_factory=dict)

    def register(self, registered: RegisteredTool) -> None:
        if registered.name in self._tools:
            raise ValueError(f"Tool '{registered.name}' already registered")
        self._tools[registered.name] = registered

    def get(self, name: str) -> RegisteredTool | None:
        return self._tools.get(name)

    def all(self) -> list[RegisteredTool]:
        return list(self._tools.values())

    def openai_schemas(self) -> list[dict]:
        return [t.to_openai_schema() for t in self._tools.values()]

    def by_group(self) -> dict[str, list[RegisteredTool]]:
        groups: dict[str, list[RegisteredTool]] = {}
        for t in self._tools.values():
            group = t.name.split("_", 1)[0]
            groups.setdefault(group, []).append(t)
        return groups


registry = ToolRegistry()


def tool(*, description: str, parameters: dict, risk: Risk, name: str | None = None):
    """Decorator that registers a plain Python function as an agent tool."""

    def decorator(func: Callable[..., Any]):
        tool_name = name or func.__name__
        registry.register(
            RegisteredTool(
                name=tool_name,
                description=description,
                parameters=parameters,
                risk=risk,
                func=func,
            )
        )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator
