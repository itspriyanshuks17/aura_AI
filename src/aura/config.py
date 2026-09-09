"""
aura/config.py
Central configuration for AURA (Autonomous Utility & Runtime Assistant).
Cross-platform by design (Windows, macOS, Linux) via `platformdirs`,
which resolves the OS-correct locations automatically:

    Linux:   ~/.config/aura/          ~/.local/share/aura/
    macOS:   ~/Library/Application Support/aura/
    Windows: %APPDATA%\\aura\\          %LOCALAPPDATA%\\aura\\

Config precedence (highest wins):
    1. Real environment variables (already set in your shell)
    2. A project-local .env (in the current directory or a parent)
    3. A global .env created by `aura --init` (~/.config/aura/.env or
       the platform equivalent) — this is what makes `aura` usable
       from any directory.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from platformdirs import user_config_dir, user_data_dir

APP_NAME = "aura"


def _load_env_layered() -> None:
    # Local project .env (dotenv searches the cwd and parent directories).
    # override=False means real env vars set in the shell always win.
    load_dotenv(override=False)

    # Global config: check aura first, fallback to legacy myai config
    aura_global = os.path.join(user_config_dir("aura"), ".env")
    myai_global = os.path.join(user_config_dir("myai"), ".env")
    if os.path.exists(aura_global):
        load_dotenv(aura_global, override=False)
    elif os.path.exists(myai_global):
        load_dotenv(myai_global, override=False)


_load_env_layered()


def _env(key: str, default: str = "") -> str:
    """Read AURA_{key} first, then fallback to MYAI_{key}, then default."""
    return os.getenv(f"AURA_{key}", os.getenv(f"MYAI_{key}", default))


def _get_bool(key: str, default: bool) -> bool:
    val = os.getenv(f"AURA_{key}", os.getenv(f"MYAI_{key}"))
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def global_config_path() -> str:
    """Where `aura --init` writes/would write the global .env."""
    return os.path.join(user_config_dir(APP_NAME), ".env")


def _default_memory_path() -> str:
    return os.path.join(user_data_dir(APP_NAME), "memory.json")


def _parse_models() -> tuple[str, ...]:
    raw = _env("MODELS", "")
    if not raw:
        raw = _env("MODEL", "")
    if "," in raw:
        return tuple(m.strip() for m in raw.split(",") if m.strip())
    if raw:
        return (raw.strip(),)
    return ()


def _default_model(provider: str) -> str:
    parsed = _parse_models()
    if parsed:
        return parsed[0]
    return "gpt-4o-mini" if provider == "openai" else "qwen3:8b"


@dataclass(frozen=True)
class Settings:
    # "ollama" -> free, local, no key needed. "openai" -> cloud, needs OPENAI_API_KEY.
    provider: str = _env("PROVIDER", "ollama")

    model: str = _default_model(_env("PROVIDER", "ollama"))

    models: tuple[str, ...] = _parse_models()

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    require_confirmation: bool = _get_bool("REQUIRE_CONFIRMATION", True)

    github_token: str = os.getenv("GITHUB_TOKEN", "")

    memory_path: str = os.path.expanduser(_env("MEMORY_PATH", _default_memory_path()))

    shell_allowlist: tuple = tuple(
        _env("SHELL_ALLOWLIST", "git docker npm pytest python python3").split()
    )

    max_tool_iterations: int = int(_env("MAX_TOOL_ITERATIONS", "8"))


settings = Settings()


def get_available_models(refresh_ollama: bool = True) -> list[str]:
    """Return a list of available models from configuration and local Ollama discovery."""
    found: list[str] = []

    # 1. Models specified in configuration
    for m in settings.models:
        if m and m not in found:
            found.append(m)

    if settings.model and settings.model not in found:
        found.insert(0, settings.model)

    # 2. Automatically query local Ollama instance if provider is ollama
    if refresh_ollama and settings.provider == "ollama":
        try:
            import json
            import urllib.request

            base = settings.ollama_base_url.rstrip("/")
            tags_url = (base[:-3] if base.endswith("/v1") else base) + "/api/tags"
            req = urllib.request.Request(tags_url, headers={"User-Agent": "AURA"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("models", []):
                    name = item.get("name")
                    if name and name not in found:
                        found.append(name)
        except Exception:
            pass

    return found or [settings.model]
