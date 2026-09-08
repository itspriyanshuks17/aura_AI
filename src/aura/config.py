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


@dataclass(frozen=True)
class Settings:
    # "ollama" -> free, local, no key needed. "openai" -> cloud, needs OPENAI_API_KEY.
    provider: str = _env("PROVIDER", "ollama")

    model: str = _env(
        "MODEL",
        "gpt-4o-mini" if _env("PROVIDER", "ollama") == "openai" else "qwen3:8b",
    )

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
