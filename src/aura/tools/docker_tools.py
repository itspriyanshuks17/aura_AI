"""
tools/docker_tools.py
Docker container management via the official Docker SDK for Python.

Deliberately NOT exposing a generic "run any docker command" tool —
each capability is its own narrow, named function so the permission
layer can reason about risk per-action instead of per-string.
"""

from __future__ import annotations

from aura.tools.registry import Risk, tool

_client = None


def _get_client():
    """Lazily create the Docker client so importing this module never
    fails just because the Docker daemon isn't running yet."""
    global _client
    if _client is None:
        import docker  # imported lazily too, in case docker isn't installed

        _client = docker.from_env()
    return _client


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - surfaced to the model as an error string
        return {"error": f"{type(exc).__name__}: {exc}"}


@tool(
    description="List all Docker containers (running and stopped) with their status and image.",
    parameters={
        "type": "object",
        "properties": {
            "all": {
                "type": "boolean",
                "description": "If true, include stopped containers too (default true).",
            }
        },
        "required": [],
    },
    risk=Risk.SAFE,
)
def docker_list_containers(all: bool = True) -> list[dict] | dict:
    def _run():
        client = _get_client()
        containers = client.containers.list(all=all)
        return [
            {
                "name": c.name,
                "id": c.short_id,
                "status": c.status,
                "image": (c.image.tags[0] if c.image.tags else c.image.short_id),
            }
            for c in containers
        ]

    return _safe(_run)


@tool(
    description="Fetch the recent log output of a specific Docker container.",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Container name or ID."},
            "tail": {
                "type": "integer",
                "description": "Number of recent log lines to fetch (default 100).",
            },
        },
        "required": ["name"],
    },
    risk=Risk.SAFE,
)
def docker_logs(name: str, tail: int = 100) -> dict:
    def _run():
        client = _get_client()
        container = client.containers.get(name)
        logs = container.logs(tail=tail).decode("utf-8", errors="replace")
        return {"name": name, "logs": logs}

    return _safe(_run)


@tool(
    description="Start a stopped Docker container.",
    parameters={
        "type": "object",
        "properties": {"name": {"type": "string", "description": "Container name or ID."}},
        "required": ["name"],
    },
    risk=Risk.CONFIRM,
)
def docker_start_container(name: str) -> dict:
    def _run():
        client = _get_client()
        client.containers.get(name).start()
        return {"result": f"Container '{name}' started."}

    return _safe(_run)


@tool(
    description="Restart a Docker container.",
    parameters={
        "type": "object",
        "properties": {"name": {"type": "string", "description": "Container name or ID."}},
        "required": ["name"],
    },
    risk=Risk.CONFIRM,
)
def docker_restart_container(name: str) -> dict:
    def _run():
        client = _get_client()
        client.containers.get(name).restart()
        return {"result": f"Container '{name}' restarted."}

    return _safe(_run)


@tool(
    description="Stop a running Docker container.",
    parameters={
        "type": "object",
        "properties": {"name": {"type": "string", "description": "Container name or ID."}},
        "required": ["name"],
    },
    risk=Risk.CONFIRM,
)
def docker_stop_container(name: str) -> dict:
    def _run():
        client = _get_client()
        client.containers.get(name).stop()
        return {"result": f"Container '{name}' stopped."}

    return _safe(_run)


@tool(
    description="Permanently remove a Docker container. This is destructive and cannot be undone.",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Container name or ID."},
            "force": {
                "type": "boolean",
                "description": "Force removal even if running (default false).",
            },
        },
        "required": ["name"],
    },
    risk=Risk.DANGEROUS,
)
def docker_remove_container(name: str, force: bool = False) -> dict:
    def _run():
        client = _get_client()
        client.containers.get(name).remove(force=force)
        return {"result": f"Container '{name}' removed."}

    return _safe(_run)


@tool(
    description="Get live resource usage stats (CPU %, memory) for a running container.",
    parameters={
        "type": "object",
        "properties": {"name": {"type": "string", "description": "Container name or ID."}},
        "required": ["name"],
    },
    risk=Risk.SAFE,
)
def docker_stats(name: str) -> dict:
    def _run():
        client = _get_client()
        container = client.containers.get(name)
        stats = container.stats(stream=False)
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        sys_delta = stats["cpu_stats"].get("system_cpu_usage", 0) - stats["precpu_stats"].get(
            "system_cpu_usage", 0
        )
        cpu_percent = (cpu_delta / sys_delta * 100.0) if sys_delta > 0 else 0.0
        mem_usage = stats["memory_stats"].get("usage", 0)
        mem_limit = stats["memory_stats"].get("limit", 1)
        return {
            "name": name,
            "cpu_percent": round(cpu_percent, 2),
            "memory_usage_mb": round(mem_usage / (1024**2), 2),
            "memory_limit_mb": round(mem_limit / (1024**2), 2),
        }

    return _safe(_run)
