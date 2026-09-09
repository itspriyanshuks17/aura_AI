"""
tools/github_tools.py
GitHub tools via PyGithub. Requires GITHUB_TOKEN to be set (a
fine-grained personal access token is recommended, scoped to only the
repos this agent should touch).
"""

from __future__ import annotations

from aura.config import settings
from aura.tools.registry import Risk, tool

_client = None


def _get_client():
    global _client
    if _client is None:
        if not settings.github_token:
            raise RuntimeError(
                "GITHUB_TOKEN is not set. Add it to your .env to enable GitHub tools."
            )
        from github import Github  # PyGithub, imported lazily

        _client = Github(settings.github_token)
    return _client


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


@tool(
    description="List the authenticated GitHub user's repositories.",
    parameters={
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "description": "Max repos to return (default 20)."}
        },
        "required": [],
    },
    risk=Risk.SAFE,
)
def github_list_repositories(limit: int = 20) -> list[dict] | dict:
    def _run():
        user = _get_client().get_user()
        repos = []
        for i, repo in enumerate(user.get_repos()):
            if i >= limit:
                break
            repos.append(
                {
                    "full_name": repo.full_name,
                    "private": repo.private,
                    "default_branch": repo.default_branch,
                    "open_issues": repo.open_issues_count,
                }
            )
        return repos

    return _safe(_run)


@tool(
    description="Get details about a specific GitHub repository (description, language, stars, forks, default branch, topics, etc.).",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."}
        },
        "required": ["repo"],
    },
    risk=Risk.SAFE,
)
def github_get_repository(repo: str) -> dict:
    def _run():
        r = _get_client().get_repo(repo)
        try:
            topics = r.get_topics()
        except Exception:
            topics = []
        return {
            "full_name": r.full_name,
            "description": r.description or "",
            "url": r.html_url,
            "private": r.private,
            "default_branch": r.default_branch,
            "language": r.language,
            "stars": r.stargazers_count,
            "forks": r.forks_count,
            "open_issues": r.open_issues_count,
            "topics": topics,
            "created_at": str(r.created_at) if r.created_at else None,
            "updated_at": str(r.updated_at) if r.updated_at else None,
        }

    return _safe(_run)


@tool(
    description="List open issues for a specific GitHub repository.",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."},
            "limit": {"type": "integer", "description": "Max issues to return (default 20)."},
        },
        "required": ["repo"],
    },
    risk=Risk.SAFE,
)
def github_list_issues(repo: str, limit: int = 20) -> list[dict] | dict:
    def _run():
        r = _get_client().get_repo(repo)
        issues = []
        for i, issue in enumerate(r.get_issues(state="open")):
            if i >= limit:
                break
            if issue.pull_request is not None:
                continue  # skip PRs, which GitHub's API also returns as "issues"
            issues.append({"number": issue.number, "title": issue.title, "url": issue.html_url})
        return issues

    return _safe(_run)


@tool(
    description="Create a new issue in a GitHub repository.",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."},
            "title": {"type": "string", "description": "Issue title."},
            "body": {"type": "string", "description": "Issue body/description."},
        },
        "required": ["repo", "title"],
    },
    risk=Risk.CONFIRM,
)
def github_create_issue(repo: str, title: str, body: str = "") -> dict:
    def _run():
        r = _get_client().get_repo(repo)
        issue = r.create_issue(title=title, body=body)
        return {"number": issue.number, "url": issue.html_url}

    return _safe(_run)


@tool(
    description="List open pull requests for a GitHub repository.",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."},
            "limit": {"type": "integer", "description": "Max PRs to return (default 20)."},
        },
        "required": ["repo"],
    },
    risk=Risk.SAFE,
)
def github_list_pull_requests(repo: str, limit: int = 20) -> list[dict] | dict:
    def _run():
        r = _get_client().get_repo(repo)
        prs = []
        for i, pr in enumerate(r.get_pulls(state="open")):
            if i >= limit:
                break
            prs.append({"number": pr.number, "title": pr.title, "url": pr.html_url})
        return prs

    return _safe(_run)


@tool(
    description="Get the status of recent GitHub Actions workflow runs for a repository.",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."},
            "limit": {"type": "integer", "description": "Max runs to return (default 5)."},
        },
        "required": ["repo"],
    },
    risk=Risk.SAFE,
)
def github_get_workflow_runs(repo: str, limit: int = 5) -> list[dict] | dict:
    def _run():
        r = _get_client().get_repo(repo)
        runs = []
        for i, run in enumerate(r.get_workflow_runs()):
            if i >= limit:
                break
            runs.append(
                {
                    "name": run.name,
                    "status": run.status,
                    "conclusion": run.conclusion,
                    "branch": run.head_branch,
                    "url": run.html_url,
                    "created_at": str(run.created_at),
                }
            )
        return runs

    return _safe(_run)
