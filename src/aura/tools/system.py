"""
tools/system.py
Read-only system diagnostics. All SAFE risk — nothing here mutates state.
"""

from __future__ import annotations

import platform

import psutil

from aura.tools.registry import Risk, tool


@tool(
    description="Get current RAM (memory) usage in GB and percent.",
    parameters={"type": "object", "properties": {}, "required": []},
    risk=Risk.SAFE,
)
def get_ram_status() -> dict:
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "usage_percent": mem.percent,
    }


@tool(
    description="Get current CPU usage percent (overall and per-core).",
    parameters={"type": "object", "properties": {}, "required": []},
    risk=Risk.SAFE,
)
def get_cpu_status() -> dict:
    per_core = psutil.cpu_percent(interval=0.3, percpu=True)
    return {
        "overall_percent": sum(per_core) / len(per_core) if per_core else 0.0,
        "per_core_percent": per_core,
        "core_count": psutil.cpu_count(logical=True),
    }


@tool(
    description="Get disk usage for the root/primary volume, in GB and percent.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Filesystem path to check (default '/').",
            }
        },
        "required": [],
    },
    risk=Risk.SAFE,
)
def get_disk_status(path: str = "/") -> dict:
    usage = psutil.disk_usage(path)
    return {
        "path": path,
        "total_gb": round(usage.total / (1024**3), 2),
        "used_gb": round(usage.used / (1024**3), 2),
        "free_gb": round(usage.free / (1024**3), 2),
        "usage_percent": usage.percent,
    }


@tool(
    description="List the top N processes by memory usage.",
    parameters={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "How many processes to return (default 10).",
            }
        },
        "required": [],
    },
    risk=Risk.SAFE,
)
def list_processes(limit: int = 10) -> list[dict]:
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda p: p.get("memory_percent") or 0, reverse=True)
    return procs[:limit]


@tool(
    description="Get basic OS/platform information (OS name, version, architecture).",
    parameters={"type": "object", "properties": {}, "required": []},
    risk=Risk.SAFE,
)
def get_os_info() -> dict:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
    }
