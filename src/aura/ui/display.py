"""ui/display.py — Rich rendering helpers for the terminal UI."""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aura.config import settings

console = Console()


def print_banner():
    banner_text = (
        "\n[bold cyan]AURA[/bold cyan]\n"
        "[bold white]Autonomous Utility & Runtime[/bold white]\n"
        "[bold white]Assistant[/bold white]\n\n"
        f"[dim]provider:[/dim] [cyan]{settings.provider}[/cyan]   "
        f"[dim]model:[/dim] [cyan]{settings.model}[/cyan]\n"
    )
    console.print(
        Panel(
            banner_text,
            box=box.ROUNDED,
            border_style="bright_blue",
            expand=False,
            padding=(0, 6),
        )
    )
    console.print(
        "[dim]Type naturally, or use /help /status /tools /history /exit[/dim]\n"
    )


def print_help():
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("/help", "Show this help")
    table.add_row("/status", "Quick system + docker snapshot")
    table.add_row("/tools", "List all available tools by group")
    table.add_row("/history", "Show this session's conversation so far")
    table.add_row("/exit", "Quit")
    console.print(table)


def print_tools(groups: dict):
    table = Table(title="Available tools")
    table.add_column("Group")
    table.add_column("Tool")
    table.add_column("Risk")
    table.add_column("Description")
    for group, tools in sorted(groups.items()):
        for t in tools:
            table.add_row(group, t.name, t.risk.value, t.description)
    console.print(table)


def print_history(messages: list[dict]):
    for m in messages:
        role = m.get("role")
        if role == "system":
            continue
        content = m.get("content")
        if not content:
            continue
        color = {"user": "green", "assistant": "cyan", "tool": "dim"}.get(role, "white")
        console.print(f"[{color}]{role}:[/{color}] {content}")
