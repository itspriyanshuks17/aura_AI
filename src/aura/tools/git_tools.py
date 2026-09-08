"""
tools/git_tools.py
Local git repository inspection and a couple of guarded mutating actions.
Uses subprocess with an explicit argv list (never shell=True, never a
raw string from the model) so there is no command-injection surface.
"""

from __future__ import annotations

import subprocess

from aura.tools.registry import Risk, tool


def _run_git(args: list[str], cwd: str | None = None) -> dict:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {"error": "git is not installed or not on PATH."}
    except subprocess.TimeoutExpired:
        return {"error": "git command timed out."}


_PATH_PARAM = {
    "path": {
        "type": "string",
        "description": "Path to the git repository (default: current directory).",
    }
}


@tool(
    description="Show git status (staged/unstaged/untracked changes) for a repository.",
    parameters={"type": "object", "properties": _PATH_PARAM, "required": []},
    risk=Risk.SAFE,
)
def git_status(path: str | None = None) -> dict:
    return _run_git(["status", "--short", "--branch"], cwd=path)


@tool(
    description="Show recent git commit history for a repository.",
    parameters={
        "type": "object",
        "properties": {
            **_PATH_PARAM,
            "limit": {"type": "integer", "description": "Number of commits to show (default 10)."},
        },
        "required": [],
    },
    risk=Risk.SAFE,
)
def git_log(path: str | None = None, limit: int = 10) -> dict:
    return _run_git(
        ["log", f"-{limit}", "--oneline", "--decorate"],
        cwd=path,
    )


@tool(
    description="Show the current uncommitted diff for a repository.",
    parameters={"type": "object", "properties": _PATH_PARAM, "required": []},
    risk=Risk.SAFE,
)
def git_diff(path: str | None = None) -> dict:
    return _run_git(["diff"], cwd=path)


@tool(
    description="List local and remote git branches for a repository.",
    parameters={"type": "object", "properties": _PATH_PARAM, "required": []},
    risk=Risk.SAFE,
)
def git_branches(path: str | None = None) -> dict:
    return _run_git(["branch", "-a"], cwd=path)


@tool(
    description="Pull the latest changes from the remote for the current branch.",
    parameters={"type": "object", "properties": _PATH_PARAM, "required": []},
    risk=Risk.CONFIRM,
)
def git_pull(path: str | None = None) -> dict:
    return _run_git(["pull"], cwd=path)


@tool(
    description="Check out a different branch (or create it) in a repository.",
    parameters={
        "type": "object",
        "properties": {
            **_PATH_PARAM,
            "branch": {"type": "string", "description": "Branch name to check out."},
            "create": {
                "type": "boolean",
                "description": "If true, create the branch if it doesn't exist (default false).",
            },
        },
        "required": ["branch"],
    },
    risk=Risk.CONFIRM,
)
def git_checkout(branch: str, path: str | None = None, create: bool = False) -> dict:
    args = ["checkout"]
    if create:
        args.append("-b")
    args.append(branch)
    return _run_git(args, cwd=path)
