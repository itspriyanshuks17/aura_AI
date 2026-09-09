"""
security/permissions.py

Sits between the agent's tool-selection and actual execution.
This is the layer that turns "the AI decided to do X" into
"X actually happened" — and it's the only place that decision is made.

    SAFE       -> auto-execute, no prompt
    CONFIRM    -> ask tool-specific confirmation (accepts Y/Yes/statements or N/No)
    DANGEROUS  -> high-risk warning (accepts Y/Yes/statements or N/No)
"""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt

from aura.config import settings
from aura.tools.registry import Risk

console = Console()


def _get_tool_prompt_details(tool_name: str, arguments: dict) -> tuple[str, str]:
    """Return a human-friendly action statement and suggested yes-phrase for a tool."""
    if tool_name == "docker_restart_container":
        name = arguments.get("name", "container")
        return f"Restart Docker container '{name}'?", "Yes, restart it"
    if tool_name == "docker_stop_container":
        name = arguments.get("name", "container")
        return f"Stop Docker container '{name}'?", "Yes, stop it"
    if tool_name == "docker_start_container":
        name = arguments.get("name", "container")
        return f"Start Docker container '{name}'?", "Yes, start it"
    if tool_name == "docker_remove_container":
        name = arguments.get("name", "container")
        return f"Permanently remove Docker container '{name}'?", "Yes, remove it"
    if tool_name == "git_checkout_branch":
        branch = arguments.get("branch", "branch")
        create = arguments.get("create", False)
        action = f"Create and checkout branch '{branch}'" if create else f"Checkout branch '{branch}'"
        return f"{action}?", "Yes, checkout"
    if tool_name == "git_commit":
        msg = arguments.get("message", "")
        return f"Commit staged changes with message '{msg}'?", "Yes, commit it"
    if tool_name == "github_create_issue":
        repo = arguments.get("repo", "")
        title = arguments.get("title", "")
        return f"Create GitHub issue '{title}' in '{repo}'?", "Yes, create issue"
    if tool_name == "memory_forget":
        key = arguments.get("key", "")
        return f"Forget saved memory key '{key}'?", "Yes, forget it"
    if tool_name == "run_shell":
        cmd = arguments.get("command", "")
        if "clone" in cmd.lower():
            return f"Run shell command to clone repository: '{cmd}'?", "Yes, clone it"
        return f"Execute shell command: '{cmd}'?", "Yes, run it"

    # Default fallback for any other tool
    clean_action = tool_name.replace("_", " ").strip()
    args_preview = ", ".join(f"{k}={v!r}" for k, v in arguments.items())
    desc = f"Run '{tool_name}' ({args_preview})" if args_preview else f"Run '{tool_name}'"
    return f"Proceed with {desc}?", f"Yes, {clean_action}"


def _is_affirmative(response: str) -> bool:
    """Return True for yes, y, true, or affirmative statements like 'Yes, clone it'."""
    cleaned = response.strip().lower()
    if not cleaned:
        return False
    # Accept standard yes values
    if cleaned in {"y", "yes", "ye", "yep", "yeah", "1", "true", "ok", "okay"}:
        return True
    # Accept phrases starting with yes / yep / yeah, e.g. "yes, clone it", "yes do it"
    if cleaned.startswith(("yes,", "yes ", "yep,", "yep ", "yeah,", "yeah ")):
        return True
    return False


def check_permission(tool_name: str, risk: Risk, arguments: dict) -> bool:
    """Return True if execution should proceed."""
    if not settings.require_confirmation:
        return True

    if risk == Risk.SAFE:
        return True

    action_text, example_phrase = _get_tool_prompt_details(tool_name, arguments)

    if risk == Risk.CONFIRM:
        console.print(f"\n[yellow]⚠  Action required:[/yellow] {action_text}")
        console.print(
            f"[dim]Respond with [bold]Y[/bold]/[bold]Yes[/bold] (e.g. '{example_phrase}'), or [bold]N[/bold]/[bold]No[/bold] to cancel.[/dim]"
        )
        answer = Prompt.ask("[bold cyan]Proceed?[/bold cyan] [y/N]", default="N")
        return _is_affirmative(answer)

    if risk == Risk.DANGEROUS:
        console.print(f"\n[bold red]⚠  DANGEROUS OPERATION:[/bold red] {action_text}")
        console.print(
            f"[dim]Respond with [bold]Y[/bold]/[bold]Yes[/bold] (e.g. '{example_phrase}'), or [bold]N[/bold]/[bold]No[/bold] to cancel.[/dim]"
        )
        answer = Prompt.ask("[bold red]Confirm execution?[/bold red] [y/N]", default="N")
        return _is_affirmative(answer)

    # Unknown risk level -> fail closed
    return False
