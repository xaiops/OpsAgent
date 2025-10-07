"""Model Context Protocol (MCP) infrastructure.

Provides client management and adapters for MCP servers.
Ready for future MCP integrations.
"""

from mcp.client import MCPClientManager, get_mcp_manager
from mcp.adapters import AAPMCPAdapter, get_aap_client

__all__ = [
    # Client
    "MCPClientManager",
    "get_mcp_manager",
    # Adapters
    "AAPMCPAdapter",
    "get_aap_client",
]
