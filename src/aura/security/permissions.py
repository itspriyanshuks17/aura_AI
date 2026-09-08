"""
security/permissions.py

Sits between the agent's tool-selection and actual execution.
This is the layer that turns "the AI decided to do X" into
"X actually happened" — and it's the only place that decision is made.

    SAFE       -> auto-execute, no prompt
    CONFIRM    -> ask a plain y/N question
    DANGEROUS  -> require the user to type an exact phrase back
"""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Confirm, Prompt

from aura.config import settings
from aura.tools.registry import Risk

console = Console()

_CONFIRM_PHRASE = "CONFIRM"


def check_permission(tool_name: str, risk: Risk, arguments: dict) -> bool:
    """Return True if execution should proceed."""
    if not settings.require_confirmation:
        return True

    if risk == Risk.SAFE:
        return True

    args_preview = ", ".join(f"{k}={v!r}" for k, v in arguments.items())

    if risk == Risk.CONFIRM:
        console.print(
            f"[yellow]⚠  '{tool_name}'[/yellow] wants to run with: {args_preview or '(no args)'}"
        )
        return Confirm.ask("Proceed?", default=False)

    if risk == Risk.DANGEROUS:
        console.print(
            f"[bold red]⚠ DANGEROUS OPERATION[/bold red]: '{tool_name}' "
            f"with: {args_preview or '(no args)'}"
        )
        console.print(f"Type [bold]{_CONFIRM_PHRASE}[/bold] to proceed, or anything else to cancel.")
        typed = Prompt.ask("Confirm")
        return typed.strip() == _CONFIRM_PHRASE

    # Unknown risk level -> fail closed
    return False
