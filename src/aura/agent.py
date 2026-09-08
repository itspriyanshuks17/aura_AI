"""
aura/agent.py

The fundamental agent loop:

    natural language -> LLM -> tool call? -> permission check -> execute
        -> result fed back to LLM -> ... -> final natural-language reply

This module owns conversation state for a single session and knows
nothing about the terminal UI — cli.py handles all display.
"""

from __future__ import annotations

import json

import aura.tools  # noqa: F401 - runs tool registration side effects
from aura.config import settings
from aura.providers.openai_compatible import get_provider
from aura.security.permissions import check_permission
from aura.tools.registry import registry as tool_registry

SYSTEM_PROMPT = """\
You are AURA (Autonomous Utility & Runtime Assistant), a personal terminal assistant with controlled access to the \
user's system, Docker, local git repos, and GitHub, through a fixed set of \
named tools. You cannot do anything outside those tools.

Rules:
- Prefer the most specific tool for the job over the generic shell tool.
- Never assume a destructive action is wanted — if the user's request is \
ambiguous about scope (e.g. "clean up my containers"), ask a clarifying \
question instead of guessing which containers they mean.
- When a tool call fails or returns an "error" field, explain the error to \
the user in plain language rather than retrying blindly.
- Keep responses concise and concrete: numbers, names, statuses. This is a \
terminal, not a chat window.
- You may use the memory_remember/memory_recall tools to keep track of \
user-specific shorthand (e.g. "backend" -> a specific container name) \
across the conversation, when the user asks you to remember something.
"""


class Agent:
    def __init__(self):
        self.provider = get_provider()
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _execute_tool_call(self, name: str, arguments: dict) -> dict:
        registered = tool_registry.get(name)
        if registered is None:
            return {"error": f"Unknown tool '{name}'."}

        allowed = check_permission(name, registered.risk, arguments)
        if not allowed:
            return {"error": f"User declined to run '{name}'."}

        try:
            result = registered.func(**arguments)
        except TypeError as exc:
            return {"error": f"Bad arguments for '{name}': {exc}"}
        except Exception as exc:  # noqa: BLE001 - surfaced to the model, not raised
            return {"error": f"{type(exc).__name__}: {exc}"}

        return result if isinstance(result, dict) else {"result": result}

    def send(self, user_input: str) -> str:
        """Send one user message through the full tool-calling loop and
        return the final assistant reply text."""
        self.messages.append({"role": "user", "content": user_input})

        tool_schemas = tool_registry.openai_schemas()

        for _ in range(settings.max_tool_iterations):
            result = self.provider.chat(self.messages, tool_schemas)

            if not result.tool_calls:
                reply = result.content or ""
                self.messages.append({"role": "assistant", "content": reply})
                return reply

            # The model wants to call one or more tools.
            self.messages.append(
                {
                    "role": "assistant",
                    "content": result.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.name, "arguments": tc.arguments},
                        }
                        for tc in result.tool_calls
                    ],
                }
            )

            for tc in result.tool_calls:
                try:
                    arguments = json.loads(tc.arguments) if tc.arguments else {}
                except json.JSONDecodeError:
                    arguments = {}

                tool_result = self._execute_tool_call(tc.name, arguments)

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(tool_result, default=str),
                    }
                )

        return (
            "Reached the max number of tool-call steps for this turn without a final "
            "answer. Try breaking your request into smaller steps."
        )
