"""
Importing this package registers every built-in tool with the shared
registry (tools.registry.registry). Add new tool modules here so they
get picked up automatically.
"""

from aura.tools import (  # noqa: F401
    docker_tools,
    git_tools,
    github_tools,
    memory_tools,
    shell_tools,
    system,
)
