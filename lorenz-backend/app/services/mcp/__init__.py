"""
LORENZ SaaS - MCP (Model Context Protocol) Integration
Enables local system execution through MCP servers
"""

from .client import MCPClient
from .manager import MCPManager
from .permissions import ExecutionPermissions, PermissionLevel

__all__ = [
    "MCPClient",
    "MCPManager",
    "ExecutionPermissions",
    "PermissionLevel",
]
