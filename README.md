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
AURA  CPU: 23% | RAM: 10.8 / 16 GB (67%) | Disk: 64% | Docker: 8 running | Git: Clean (1.42s)

aura > show unhealthy docker containers
AURA  ⚠ backend-api is unhealthy (0.85s)

aura > restart it
⚠  'docker_restart_container' wants to run with: name='backend-api'
Proceed? [y/N]: y
AURA  Restarted 'backend-api' successfully. (2.10s)
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

Requires **Python 3.10+** and [git](https://github.com/itspriyanshuks17/aura_AI.git).

```bash
git clone https://github.com/itspriyanshuks17/aura_AI.git && cd aura_AI
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

### GitHub AI Suite (optional)

Set `GITHUB_TOKEN` in your `.env` to enable full GitHub integration. AURA features 17 specialized GitHub tools:

- **Users & Organizations**:
  - `github_get_user`: View any GitHub user or organization profile (bio, company, location, public repos count, followers, hireable status, creation date).
  - `github_list_user_repositories`: List public repos belonging to any specific GitHub user or org.
  - `github_list_repositories`: List repositories for the authenticated user.
- **Repositories, Code & Search**:
  - `github_get_repository`: Detailed repository metadata (stars, forks, open issues, language, topics, default branch).
  - `github_get_file_content`: Read and decode any file (e.g. `README.md`, `pyproject.toml`, source code) directly from GitHub.
  - `github_list_directory_contents`: Browse files and subdirectories within a repository path.
  - `github_search_repositories`: Search GitHub repositories by keyword, language, or topic.
- **Commits & Releases**:
  - `github_list_commits`: View recent commit history, authors, and commit messages.
  - `github_get_latest_release`: Inspect the latest release tag, release notes, and published assets.
- **Issues & Discussions**:
  - `github_get_issue`: Full issue details, labels, author, and recent discussion comments.
  - `github_list_issues`: List open issues for any repository.
  - `github_create_issue`: Open a new issue (*requires confirmation*).
  - `github_add_issue_comment`: Add a comment to an existing issue or pull request (*requires confirmation*).
- **Pull Requests & CI/CD**:
  - `github_get_pull_request`: Full PR details (mergeable status, changed files, additions/deletions, branches).
  - `github_list_pull_requests`: List open PRs for any repository.
  - `github_create_pull_request`: Open a new pull request (*requires confirmation*).
  - `github_get_workflow_runs`: Check recent GitHub Actions CI/CD workflow run statuses.

#### Example GitHub Prompts in AURA:
```text
aura > tell me about itspriyanshuks17
aura > what repositories does itspriyanshuks17 have?
aura > read the README.md in itspriyanshuks17/azure_learning
aura > show the latest commits on itspriyanshuks17/azure_learning
aura > search github for popular docker terminal agents
aura > check open issues on Interns-MQI-25/.github-private
```

### Response Duration Tracking

Both interactive REPL and one-shot commands automatically measure and print elapsed execution time in seconds (e.g. `(1.42s)`), so you can monitor latency across local models and API backends.

### Multi-Model Support & Dynamic Switching

You can configure multiple models to choose from, or dynamically switch between local and cloud models at runtime:
- **Configure in `.env`**: Set `AURA_MODELS=llama3.2:3b, qwen3:8b, gpt-4o-mini` to populate a selectable list. If not specified, AURA auto-discovers all locally installed Ollama models.
- **Interactive Startup Picker**: Launch with `aura --select-model` (or configure multiple `AURA_MODELS`) to choose your active model on launch.
- **In-Chat Switching**: Use `/model` to view all available models, or `/model <name|#>` to switch instantly without losing conversation history.

## Usage

```bash
aura                       # interactive REPL
aura --select-model        # pick from available models interactively at launch
aura "your prompt here"    # one-shot: answer and exit (scriptable)
aura --version
aura --help
aura --provider openai --model gpt-4o-mini "your prompt"   # one-off override
aura --no-confirm "your prompt"   # skip confirmation prompts (use with care)
```

Inside the REPL: `/help`, `/model`, `/status`, `/tools`, `/history`, `/exit`.

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

AURA never runs arbitrary or unverified shell strings. Every capability is exposed through a strictly typed and schema-validated tool with context-aware confirmation:

| Risk          | Behavior                                                                                       | Accepted Responses                                                    |
| ------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `SAFE`        | Executes immediately (read-only diagnostics, status, lists, logs)                              | None required                                                         |
| `CONFIRM`     | Shows tool-specific question (e.g. *Restart container 'backend'?*) and asks `[y/N]`            | `Y`, `Yes`, `yep`, `N`, `No`, or statements like *"Yes, restart it"* |
| `DANGEROUS`   | Displays high-risk warning with action statement (container deletion, restricted shell command) | `Y`, `Yes`, `N`, `No`, or statements like *"Yes, clone it"*           |

## Project layout

```
aura/
├── pyproject.toml        # Hatchling build definition & scripts
├── requirements.txt
├── CHANGELOG.md          # Release history and feature changes
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
