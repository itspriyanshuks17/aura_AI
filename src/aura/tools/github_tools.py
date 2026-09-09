"""
tools/github_tools.py
GitHub tools via PyGithub. Requires GITHUB_TOKEN to be set in your environment
or .env (a personal access token scoped to the repositories you want to manage).
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


# ── Users & Organizations ─────────────────────────────────────────────


@tool(
    description="Get public profile information about any GitHub user or organization (name, bio, company, location, public repos, followers, etc.). If username is omitted, returns the authenticated user's profile.",
    parameters={
        "type": "object",
        "properties": {
            "username": {
                "type": "string",
                "description": "GitHub username (e.g. 'itspriyanshuks17', 'torvalds'). Leave empty for authenticated user.",
            }
        },
        "required": [],
    },
    risk=Risk.SAFE,
)
def github_get_user(username: str = "") -> dict:
    def _run():
        g = _get_client()
        u = g.get_user(username.strip()) if username.strip() else g.get_user()
        return {
            "login": u.login,
            "name": u.name or u.login,
            "bio": u.bio or "",
            "company": u.company or "",
            "location": u.location or "",
            "blog": u.blog or "",
            "email": u.email or "",
            "public_repos": u.public_repos,
            "followers": u.followers,
            "following": u.following,
            "created_at": str(u.created_at) if u.created_at else None,
            "url": u.html_url,
        }

    return _safe(_run)


@tool(
    description="List public repositories belonging to a specific GitHub user or organization.",
    parameters={
        "type": "object",
        "properties": {
            "username": {"type": "string", "description": "GitHub username or organization name."},
            "limit": {"type": "integer", "description": "Max repos to return (default 20)."},
        },
        "required": ["username"],
    },
    risk=Risk.SAFE,
)
def github_list_user_repositories(username: str, limit: int = 20) -> list[dict] | dict:
    def _run():
        u = _get_client().get_user(username.strip())
        repos = []
        for i, repo in enumerate(u.get_repos()):
            if i >= limit:
                break
            repos.append(
                {
                    "full_name": repo.full_name,
                    "description": repo.description or "",
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "language": repo.language,
                    "default_branch": repo.default_branch,
                    "url": repo.html_url,
                }
            )
        return repos

    return _safe(_run)


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


# ── Repository Details & Inspection ───────────────────────────────────


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
    description="Get and decode the text content of a file from a GitHub repository (e.g. 'README.md', 'pyproject.toml', or source files). Content is truncated if too large.",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."},
            "path": {"type": "string", "description": "Path to file in the repo (e.g. 'README.md', 'src/main.py')."},
            "ref": {"type": "string", "description": "Branch, tag, or commit SHA (optional, defaults to default branch)."},
        },
        "required": ["repo", "path"],
    },
    risk=Risk.SAFE,
)
def github_get_file_content(repo: str, path: str, ref: str = "") -> dict:
    def _run():
        r = _get_client().get_repo(repo)
        kwargs = {"ref": ref} if ref else {}
        contents = r.get_contents(path, **kwargs)
        if isinstance(contents, list):
            return {
                "error": f"'{path}' is a directory, not a file. Use github_list_directory_contents instead."
            }
        decoded = contents.decoded_content.decode("utf-8", errors="replace")
        max_chars = 10000
        truncated = len(decoded) > max_chars
        return {
            "path": contents.path,
            "size": contents.size,
            "truncated": truncated,
            "content": decoded[:max_chars] + ("\n... [Truncated for context length]" if truncated else ""),
        }

    return _safe(_run)


@tool(
    description="List files and directories in a repository path.",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."},
            "path": {"type": "string", "description": "Directory path (leave empty for repository root)."},
            "ref": {"type": "string", "description": "Branch, tag, or commit SHA (optional)."},
        },
        "required": ["repo"],
    },
    risk=Risk.SAFE,
)
def github_list_directory_contents(repo: str, path: str = "", ref: str = "") -> list[dict] | dict:
    def _run():
        r = _get_client().get_repo(repo)
        kwargs = {"ref": ref} if ref else {}
        contents = r.get_contents(path or "", **kwargs)
        if not isinstance(contents, list):
            contents = [contents]
        items = []
        for item in contents:
            items.append(
                {
                    "name": item.name,
                    "path": item.path,
                    "type": item.type,
                    "size": item.size,
                    "url": item.html_url,
                }
            )
        return items

    return _safe(_run)


@tool(
    description="Search GitHub repositories matching a keyword, topic, or query string.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "GitHub search query (e.g. 'topic:agent language:python', 'azure learning user:itspriyanshuks17').",
            },
            "limit": {"type": "integer", "description": "Max results to return (default 10)."},
        },
        "required": ["query"],
    },
    risk=Risk.SAFE,
)
def github_search_repositories(query: str, limit: int = 10) -> list[dict] | dict:
    def _run():
        g = _get_client()
        results = []
        for i, repo in enumerate(g.search_repositories(query)):
            if i >= limit:
                break
            results.append(
                {
                    "full_name": repo.full_name,
                    "description": repo.description or "",
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "language": repo.language,
                    "url": repo.html_url,
                }
            )
        return results

    return _safe(_run)


# ── Commits & Releases ───────────────────────────────────────────────


@tool(
    description="List recent commits for a GitHub repository.",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."},
            "limit": {"type": "integer", "description": "Max commits to return (default 10)."},
            "branch": {"type": "string", "description": "Branch name or SHA (optional)."},
        },
        "required": ["repo"],
    },
    risk=Risk.SAFE,
)
def github_list_commits(repo: str, limit: int = 10, branch: str = "") -> list[dict] | dict:
    def _run():
        r = _get_client().get_repo(repo)
        kwargs = {"sha": branch} if branch else {}
        commits = []
        for i, c in enumerate(r.get_commits(**kwargs)):
            if i >= limit:
                break
            author_name = c.commit.author.name if c.commit.author else "Unknown"
            commit_date = str(c.commit.author.date) if c.commit.author else ""
            message = c.commit.message.split("\n")[0]
            commits.append(
                {
                    "sha": c.sha[:7],
                    "author": author_name,
                    "date": commit_date,
                    "message": message,
                    "url": c.html_url,
                }
            )
        return commits

    return _safe(_run)


@tool(
    description="Get the latest release for a GitHub repository.",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."}
        },
        "required": ["repo"],
    },
    risk=Risk.SAFE,
)
def github_get_latest_release(repo: str) -> dict:
    def _run():
        r = _get_client().get_repo(repo)
        rel = r.get_latest_release()
        return {
            "tag_name": rel.tag_name,
            "name": rel.title or rel.tag_name,
            "published_at": str(rel.published_at) if rel.published_at else None,
            "body": rel.body[:2000] if rel.body else "",
            "assets_count": rel.raw_data.get("assets", []).__len__() if hasattr(rel, "raw_data") else 0,
            "url": rel.html_url,
        }

    return _safe(_run)


# ── Issues ───────────────────────────────────────────────────────────


@tool(
    description="Get detailed information and recent discussion comments for a specific GitHub issue.",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."},
            "number": {"type": "integer", "description": "Issue number."},
        },
        "required": ["repo", "number"],
    },
    risk=Risk.SAFE,
)
def github_get_issue(repo: str, number: int) -> dict:
    def _run():
        r = _get_client().get_repo(repo)
        issue = r.get_issue(number)
        comments = []
        for i, c in enumerate(issue.get_comments()):
            if i >= 5:
                break
            comments.append(
                {
                    "author": c.user.login if c.user else "unknown",
                    "created_at": str(c.created_at),
                    "body": c.body[:500] if c.body else "",
                }
            )
        return {
            "number": issue.number,
            "title": issue.title,
            "state": issue.state,
            "author": issue.user.login if issue.user else "unknown",
            "body": issue.body or "",
            "labels": [label.name for label in issue.labels],
            "comments_count": issue.comments,
            "recent_comments": comments,
            "url": issue.html_url,
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
    description="Add a comment to an existing GitHub issue or pull request.",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."},
            "number": {"type": "integer", "description": "Issue or Pull Request number."},
            "body": {"type": "string", "description": "Comment text to post."},
        },
        "required": ["repo", "number", "body"],
    },
    risk=Risk.CONFIRM,
)
def github_add_issue_comment(repo: str, number: int, body: str) -> dict:
    def _run():
        r = _get_client().get_repo(repo)
        issue = r.get_issue(number)
        comment = issue.create_comment(body)
        return {"id": comment.id, "url": comment.html_url}

    return _safe(_run)


# ── Pull Requests ────────────────────────────────────────────────────


@tool(
    description="Get details for a specific GitHub pull request.",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."},
            "number": {"type": "integer", "description": "Pull request number."},
        },
        "required": ["repo", "number"],
    },
    risk=Risk.SAFE,
)
def github_get_pull_request(repo: str, number: int) -> dict:
    def _run():
        r = _get_client().get_repo(repo)
        pr = r.get_pull(number)
        return {
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "author": pr.user.login if pr.user else "unknown",
            "body": pr.body or "",
            "mergeable": pr.mergeable,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files,
            "base_branch": pr.base.ref,
            "head_branch": pr.head.ref,
            "url": pr.html_url,
        }

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
    description="Open a new pull request in a GitHub repository.",
    parameters={
        "type": "object",
        "properties": {
            "repo": {"type": "string", "description": "Repo in 'owner/name' format."},
            "title": {"type": "string", "description": "Pull request title."},
            "head": {"type": "string", "description": "The name of the branch where your changes are implemented."},
            "base": {"type": "string", "description": "The branch you want to merge into (default 'main')."},
            "body": {"type": "string", "description": "Pull request description (optional)."},
        },
        "required": ["repo", "title", "head"],
    },
    risk=Risk.CONFIRM,
)
def github_create_pull_request(repo: str, title: str, head: str, base: str = "main", body: str = "") -> dict:
    def _run():
        r = _get_client().get_repo(repo)
        pr = r.create_pull(title=title, body=body, head=head, base=base)
        return {"number": pr.number, "url": pr.html_url, "state": pr.state}

    return _safe(_run)


# ── Actions & Workflows ──────────────────────────────────────────────


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
