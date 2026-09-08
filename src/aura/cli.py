"""
aura/cli.py — the `aura` command's entry point.

Behaves like the CLI tools this is modeled after:

    aura                        interactive REPL
    aura "check my ram usage"   one-shot: answer and exit (scriptable)
    aura --version
    aura --init                 write a global config file you can edit
    aura --provider openai --model gpt-4o-mini   one-off overrides

Argument parsing and any environment overrides happen BEFORE importing
aura.agent / aura.config, since Settings reads os.environ at import time.
"""

from __future__ import annotations

import argparse
import os
import sys

from aura import __version__

GLOBAL_ENV_TEMPLATE = """\
# AURA global config — created by `aura --init`.
# A project-local .env in whatever directory you run `aura` from will
# override any of these. Real shell environment variables override both.

AURA_PROVIDER=ollama
AURA_MODEL=qwen3:8b

OLLAMA_BASE_URL=http://localhost:11434/v1

OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1

GITHUB_TOKEN=

AURA_REQUIRE_CONFIRMATION=true
AURA_SHELL_ALLOWLIST=git docker npm pytest python python3
AURA_MAX_TOOL_ITERATIONS=8
"""


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aura",
        description="AURA — Autonomous Utility & Runtime Assistant: A personal terminal "
        "AI agent with controlled access to your system, Docker, git, and GitHub — "
        "free via local Ollama or OpenAI's API.",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Run a single prompt and print the answer, then exit (scriptable, "
        "one-shot mode). If omitted, starts the interactive REPL.",
    )
    parser.add_argument(
        "--version", action="store_true", help="Print the version and exit."
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Create a global config file (~/.config/aura/.env or the platform "
        "equivalent) and exit.",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "ollama"],
        help="Override AURA_PROVIDER for this run.",
    )
    parser.add_argument("--model", help="Override AURA_MODEL for this run.")
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip all confirmation prompts for this run. Use with care — "
        "CONFIRM/DANGEROUS tools will execute immediately.",
    )
    return parser


def _run_init() -> None:
    # Imported here (not at module top) purely so `aura --version` and
    # `--help` stay fast and don't need platformdirs/rich resolved first.
    from rich.console import Console

    from aura.config import global_config_path

    console = Console()
    target = global_config_path()

    if os.path.exists(target):
        console.print(f"[yellow]Config already exists at[/yellow] {target}")
        console.print("[dim]Delete it first if you want to regenerate it.[/dim]")
        return

    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(GLOBAL_ENV_TEMPLATE)

    console.print(f"[green]Created config at[/green] {target}")
    console.print(
        "Edit it to set your provider/model (or GITHUB_TOKEN for GitHub tools), "
        "then just run [bold]aura[/bold] from anywhere."
    )


def _run_one_shot(prompt: str) -> None:
    from aura.agent import Agent
    from aura.ui.display import console

    try:
        agent = Agent()
    except Exception as exc:  # noqa: BLE001
        console.print(f"[bold red]Failed to start:[/bold red] {exc}")
        sys.exit(1)

    with console.status("[dim]thinking...[/dim]"):
        reply = agent.send(prompt)
    console.print(reply)


def _run_repl() -> None:
    from rich.prompt import Prompt

    from aura.agent import Agent
    from aura.tools.registry import registry as tool_registry
    from aura.ui.display import console, print_banner, print_help, print_history, print_tools

    print_banner()

    try:
        agent = Agent()
    except Exception as exc:  # noqa: BLE001
        console.print(f"[bold red]Failed to start:[/bold red] {exc}")
        console.print(
            "[dim]Run `aura --init` to create a config file, or check your "
            "project .env — see .env.example for the available settings.[/dim]"
        )
        sys.exit(1)

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]aura[/bold cyan] >")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye[/dim]")
            break

        stripped = user_input.strip()
        if not stripped:
            continue

        if stripped in {"/exit", "/quit"}:
            console.print("[dim]bye[/dim]")
            break
        if stripped == "/help":
            print_help()
            continue
        if stripped == "/tools":
            print_tools(tool_registry.by_group())
            continue
        if stripped == "/history":
            print_history(agent.messages)
            continue
        if stripped == "/status":
            user_input = (
                "Give me a quick status snapshot: RAM, CPU, disk usage, and the list "
                "of docker containers with their status."
            )

        with console.status("[dim]thinking...[/dim]"):
            reply = agent.send(user_input)

        console.print(f"[bold cyan]AURA[/bold cyan]  {reply}")


def main(argv: list[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"aura {__version__}")
        return

    if args.init:
        _run_init()
        return

    # Apply one-off overrides BEFORE anything imports aura.config, since
    # Settings reads os.environ at import time.
    if args.provider:
        os.environ["AURA_PROVIDER"] = args.provider
        os.environ["MYAI_PROVIDER"] = args.provider
    if args.model:
        os.environ["AURA_MODEL"] = args.model
        os.environ["MYAI_MODEL"] = args.model
    if args.no_confirm:
        os.environ["AURA_REQUIRE_CONFIRMATION"] = "false"
        os.environ["MYAI_REQUIRE_CONFIRMATION"] = "false"

    if args.prompt:
        _run_one_shot(" ".join(args.prompt))
    else:
        _run_repl()


if __name__ == "__main__":
    main()
