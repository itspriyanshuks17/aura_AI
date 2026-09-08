"""
tools/shell_tools.py

A DELIBERATELY RESTRICTED shell escape hatch — NOT a generic
"run any command" tool. Per the architecture this project follows:
generic shell access is how an agent ends up running
`docker system prune -af` when you asked it to "clean things up".

Rules enforced here, in order:
  1. The first token of the command must be in the configured allowlist
     (default: git, docker, npm, pytest, python, python3).
  2. The full command string is checked against a blocklist of
     dangerous substrings (rm -rf, mkfs, shutdown, format, diskpart,
     reg delete, etc.) regardless of the leading program.
  3. Risk is always DANGEROUS — the permission layer will demand an
     exact typed confirmation phrase before anything runs.

Prefer adding a proper named tool (like the docker_* or git_* tools)
over reaching for this. This exists only for the long tail of
one-off commands that don't justify their own tool yet.
"""

from __future__ import annotations

import os
import shlex
import subprocess

from aura.config import settings
from aura.tools.registry import Risk, tool

_BLOCKLIST_SUBSTRINGS = [
    "rm -rf",
    "rm -fr",
    "mkfs",
    "dd if=",
    "shutdown",
    "reboot",
    "format ",
    "diskpart",
    "reg delete",
    ":(){:|:&};:",  # fork bomb
    "> /dev/sda",
    "chmod -R 777 /",
]


@tool(
    description=(
        "Run a single restricted shell command. Only use this when no dedicated tool "
        "covers the task. The leading command must be one of: "
        + ", ".join(settings.shell_allowlist)
        + ". Always destructive-by-policy: the user must type an exact confirmation "
        "phrase before it executes."
    ),
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The full shell command to run, e.g. 'git status'.",
            }
        },
        "required": ["command"],
    },
    risk=Risk.DANGEROUS,
)
def run_shell(command: str) -> dict:
    lowered = command.lower()
    for bad in _BLOCKLIST_SUBSTRINGS:
        if bad in lowered:
            return {"error": f"Refused: command matches blocked pattern '{bad}'."}

    try:
        tokens = shlex.split(command, posix=(os.name != "nt"))
    except ValueError as exc:
        return {"error": f"Could not parse command: {exc}"}

    if not tokens:
        return {"error": "Empty command."}

    leading = tokens[0]
    if leading not in settings.shell_allowlist:
        return {
            "error": (
                f"Refused: '{leading}' is not in the allowlist "
                f"({', '.join(settings.shell_allowlist)})."
            )
        }

    try:
        result = subprocess.run(tokens, capture_output=True, text=True, timeout=60)
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 60s."}
    except FileNotFoundError:
        return {"error": f"'{leading}' is not installed or not on PATH."}
