"""MCP server adapters.

Each adapter provides a clean interface for interacting with a specific MCP server.
"""

from mcp.adapters.aap_adapter import AAPMCPAdapter, get_aap_client

__all__ = [
    "AAPMCPAdapter",
    "get_aap_client",
]
