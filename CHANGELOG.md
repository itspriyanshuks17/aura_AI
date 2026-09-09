# Changelog

All notable changes to the AURA project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **`github_get_repository` Tool** (`src/aura/tools/github_tools.py`):
  - Fetches complete metadata for a specific repository (`owner/name`).
  - Retrieves description, primary language, star count, fork count, open issues count, topics/tags, default branch, and timestamps (`created_at`, `updated_at`).
  - Enables AURA to answer general repository inquiries directly instead of falling back to issue/PR listings.
- **Response Latency & Execution Timer** (`src/aura/cli.py`):
  - Tracks elapsed turn time with high-resolution `time.perf_counter()`.
  - Displays elapsed seconds at the end of every assistant reply in both interactive REPL and one-shot CLI mode (e.g., `(1.42s)`).
- **Workspace IDE Configuration** (`.vscode/settings.json`):
  - Configured workspace interpreter to automatically point to `.venv/Scripts/python.exe` and added `src/` to analysis extra paths, eliminating language server "Cannot find module" diagnostics.
- **Multi-Model Selection & Dynamic Switching** (`src/aura/config.py`, `src/aura/providers/openai_compatible.py`, `src/aura/agent.py`, `src/aura/cli.py`, `src/aura/ui/display.py`):
  - Supported `AURA_MODELS` (comma-separated list of models) in `.env` and configuration.
  - Added automatic local model discovery from Ollama (`/api/tags`) when no explicit list is configured.
  - Added interactive startup model picker (`--select-model` or when multiple `AURA_MODELS` are configured).
  - Added `/model` and `/model <name|#>` commands in the interactive REPL to inspect and switch active models on the fly without session restarts.
  - Automatically handles switching between local Ollama and cloud OpenAI backends based on the chosen model name.
- **Dynamic Tool-Specific Confirmations & Flexible Y/N Inputs** (`src/aura/security/permissions.py`):
  - Replaced the rigid `"Type CONFIRM to proceed"` prompt with human-readable, tool-specific action questions (e.g. *Restart Docker container 'xyz'?*, *Run shell command to clone repository: 'git clone ...'?*).
  - Provides contextual suggested response phrases for each tool (e.g. *"Yes, clone it"*, *"Yes, restart it"*).
  - Accepts flexible affirmative inputs: `Y`, `y`, `Yes`, `yes`, `yep`, or complete statements starting with affirmative keywords (e.g. `"Yes, clone it"`, `"yes, do it"`), while declining on `N`, `no`, or empty input.
