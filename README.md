# AURA — Autonomous Utility & Runtime Assistant

A terminal AI agent you install once and run from anywhere on **Windows, macOS, or Linux** — with controlled access to your system, Docker, git, and GitHub, and free to run entirely locally if you want (via [Ollama](https://ollama.com)) or with OpenAI.

```
$ aura
╭──────────────────────────────────────────────╮
│                                              │
│                    AURA                      │
│        Autonomous Utility & Runtime          │
│                  Assistant                   │
│                                              │
│  provider: ollama  model: qwen3:8b           │
╰──────────────────────────────────────────────╯

aura > check my system
AURA  CPU: 23% | RAM: 10.8 / 16 GB (67%) | Disk: 64% | Docker: 8 running | Git: Clean

aura > show unhealthy docker containers
AURA  ⚠ backend-api is unhealthy

aura > restart it
⚠  'docker_restart_container' wants to run with: name='backend-api'
Proceed? [y/N]: y
AURA  Restarted 'backend-api' successfully.
```

Or non-interactively, for scripts:

```bash
$ aura "check my ram usage"
You're using 11.2 GB / 16 GB (70%).
```

## Why AURA?

- **Autonomous** → Decides which action and tool to execute based on your prompt.
- **Utility** → System diagnostics, Docker, Git, GitHub, networking, etc.
- **Runtime** → Direct, guarded interaction with your running environment.
- **Assistant** → Natural-language interface designed specifically for engineers and developers.

## Install

Requires **Python 3.10+** and [git](https://git-scm.com/downloads).

```bash
git clone <this-repo-url> aura && cd aura
```

### Recommended: pipx (isolated global CLI)

```bash
python -m pip install --user pipx
python -m pipx ensurepath
python -m pipx install --editable .
```

### Alternative: plain pip

```bash
pip install -e .
```

This installs the **`aura` command** globally on your PATH. Test it with:

```bash
aura --version
```

## First-time setup

```bash
aura --init
```

This writes a global config file to your platform-specific directory:

| OS      | Location                                      |
| ------- | --------------------------------------------- |
| Linux   | `~/.config/aura/.env`                        |
| macOS   | `~/Library/Application Support/aura/.env`     |
| Windows | `%LOCALAPPDATA%\aura\.env`                    |

### Option A — Free & local via Ollama (default)

1. Install [Ollama](https://ollama.com/download).
2. Pull a tool-calling-capable model:
   ```bash
   ollama pull qwen3:8b
   ```
3. Start Ollama (`ollama serve`).
4. That's it! `aura` is ready to go.

### Option B — OpenAI cloud

Edit `%LOCALAPPDATA%\aura\.env` (or set in local `.env`):

```ini
AURA_PROVIDER=openai
AURA_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

Or pass flags per-run: `aura --provider openai --model gpt-4o-mini`

### GitHub tools (optional)

Set `GITHUB_TOKEN` in your `.env` to enable GitHub issue, PR, repository, and workflow inspection.

## Usage

```bash
aura                       # interactive REPL
aura "your prompt here"    # one-shot: answer and exit (scriptable)
aura --version
aura --help
aura --provider openai --model gpt-4o-mini "your prompt"   # one-off override
aura --no-confirm "your prompt"   # skip confirmation prompts (use with care)
```

Inside the REPL: `/help`, `/status`, `/tools`, `/history`, `/exit`.

### Architecture

```
AURA
├── AURA Core
│   └── Agent / LLM / Conversation Loop
├── AURA System
│   └── CPU / RAM / Disk / Processes (psutil)
├── AURA Docker
│   └── Containers / Images / Logs / Stats (Docker SDK)
├── AURA Git
│   └── Branches / Commits / Diff / Status
├── AURA GitHub
│   └── Repos / Issues / PRs / Actions (PyGithub)
├── AURA Security
│   └── Risk Levels: SAFE / CONFIRM / DANGEROUS
└── AURA Memory
    └── Persistent shorthand & user preferences
```

### Security & Risk Levels

AURA never runs arbitrary or unverified shell strings. Every capability is exposed through a strictly typed and schema-validated tool:

| Risk          | Behavior                                                                   |
| ------------- | -------------------------------------------------------------------------- |
| `SAFE`      | Executes immediately (read-only diagnostics, status, lists, logs)          |
| `CONFIRM`   | Displays intended parameters and asks `[y/N]` before proceeding           |
| `DANGEROUS` | Requires typing `CONFIRM` explicitly (container removals, shell fallback)  |

## Project layout

```
aura/
├── pyproject.toml        # Hatchling build definition & scripts
├── requirements.txt
├── .env.example
└── src/aura/
    ├── cli.py             # CLI entry point (REPL + one-shot + init)
    ├── agent.py           # Agent loop & tool execution orchestration
    ├── config.py          # Cross-platform settings (platformdirs)
    ├── providers/openai_compatible.py
    ├── security/permissions.py
    ├── tools/             # system, docker, git, github, memory, shell
    └── ui/display.py      # Rich terminal formatting & panels
```
