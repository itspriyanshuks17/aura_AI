"""
providers/openai_compatible.py

One client class for two backends:
  - OpenAI's cloud API (paid, needs OPENAI_API_KEY)
  - A local Ollama server (free, runs on your machine, zero API cost)

This works because Ollama exposes an OpenAI-compatible /v1 endpoint,
including tool/function calling for models that support it (e.g. Qwen3,
Llama 3.1+, Mistral). So the rest of the app just calls `provider.chat(...)`
and never has to branch on which backend is active.
"""

from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from aura.config import settings


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str  # raw JSON string, as returned by the API


@dataclass
class ChatResult:
    content: str | None
    tool_calls: list[ToolCall]


class Provider:
    def __init__(self):
        if settings.provider == "openai":
            if not settings.openai_api_key:
                raise RuntimeError(
                    "AURA_PROVIDER=openai but OPENAI_API_KEY is not set. "
                    "Either set the key, or switch AURA_PROVIDER=ollama for a free local model."
                )
            self._client = OpenAI(
                api_key=settings.openai_api_key, base_url=settings.openai_base_url
            )
        elif settings.provider == "ollama":
            # Ollama ignores the API key but the client requires a non-empty string
            self._client = OpenAI(api_key="ollama", base_url=settings.ollama_base_url)
        else:
            raise ValueError(f"Unknown AURA_PROVIDER: {settings.provider!r}")

        self.model = settings.model

    def chat(self, messages: list[dict], tools: list[dict]) -> ChatResult:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or None,
        )
        choice = response.choices[0]
        message = choice.message

        tool_calls = []
        for tc in getattr(message, "tool_calls", None) or []:
            tool_calls.append(
                ToolCall(id=tc.id, name=tc.function.name, arguments=tc.function.arguments)
            )

        return ChatResult(content=message.content, tool_calls=tool_calls)


def get_provider() -> Provider:
    return Provider()
