"""MCP Client Manager for managing multiple MCP server connections.

This module provides infrastructure for connecting to and managing
Model Context Protocol (MCP) servers using langchain-mcp-adapters.

=== WHAT IS MCP? ===
Model Context Protocol (MCP) is an open protocol that standardizes how
applications provide context to LLMs. Instead of hardcoding tools, MCP
servers expose tools dynamically that LLMs can discover and use.

=== HOW IT WORKS ===
1. Agent calls MCPClientManager.initialize(server_configs)
2. MCPClientManager creates MultiServerMCPClient (from langchain-mcp-adapters)
3. MultiServerMCPClient connects to MCP server via HTTP (streamable_http transport)
4. MCP server returns list of available tools in MCP protocol format
5. langchain-mcp-adapters converts MCP tools → LangChain BaseTool format
6. Agent passes these tools to create_react_agent()
7. LLM can now call these tools as if they were local functions
8. When LLM invokes a tool, the call goes: LLM → LangChain → MCP Client → MCP Server

=== WHY ASYNC? ===
MCP uses HTTP for communication. All HTTP calls are async to avoid blocking
the agent while waiting for tool discovery or tool execution responses.

Official docs:
- https://langchain-ai.github.io/langgraph/how-tos/mcp/
- https://github.com/langchain-ai/langchain-mcp-adapters
- https://modelcontextprotocol.io/
"""

import logging
from typing import Dict, List, Optional, Any
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)


class MCPClientManager:
    """
    Manages connections to multiple MCP servers using MultiServerMCPClient.
    
    This follows the official LangGraph pattern for MCP integration:
    1. Connect to configured MCP servers
    2. Dynamically discover available tools
    3. Return LangChain-compatible tools for agent use
    """
    
    def __init__(self):
        self._client: Optional[MultiServerMCPClient] = None
        self._tools_cache: Optional[List[Any]] = None
        self._initialized = False
        
    async def initialize(self, server_configs: Dict[str, Any]) -> None:
        """
        Initialize connections to MCP servers using MultiServerMCPClient.
        
        This method:
        1. Filters enabled servers from config
        2. Converts config format to MultiServerMCPClient connection format
        3. Creates MultiServerMCPClient with all enabled servers
        4. Calls get_tools() to discover available tools from all servers
        5. Caches tools for use by the agent
        
        Transport types:
        - "streamable_http": HTTP transport for remote MCP servers (most common)
        - "stdio": Standard input/output for local MCP servers
        
        Args:
            server_configs: Dictionary of server name -> MCPServerConfig
            
        Example:
            {
                "aap_ansible": {
                    "url": "http://localhost:9005/mcp",
                    "transport": "streamable_http",
                    "enabled": True
                }
            }
        """
        if self._initialized:
            logger.warning("MCPClientManager already initialized")
            return
        
        # Filter enabled servers and convert to MultiServerMCPClient format
        connections = {}
        for server_name, config in server_configs.items():
            if config.get("enabled", False):
                connection_config = {
                    "url": config["url"],
                    "transport": config["transport"],
                }
                
                # Add optional headers if present
                if "headers" in config:
                    connection_config["headers"] = config["headers"]
                    
                connections[server_name] = connection_config
                logger.info(f"Configured MCP server: {server_name} at {config['url']}")
        
        if not connections:
            logger.warning("No enabled MCP servers found")
            self._initialized = True
            return
        
        logger.info(f"Initializing MultiServerMCPClient with {len(connections)} server(s)")
        
        try:
            # Create MultiServerMCPClient as per official docs
            self._client = MultiServerMCPClient(connections)
            
            # Load tools from all configured servers
            self._tools_cache = await self._client.get_tools()
            
            logger.info(f"Successfully loaded {len(self._tools_cache)} tools from MCP servers")
            logger.info(f"Available MCP tools: {[tool.name for tool in self._tools_cache]}")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}", exc_info=True)
            self._initialized = False
            raise
        
    async def get_tools(self, server_name: Optional[str] = None) -> List[Any]:
        """
        Get tools from MCP servers.
        
        Args:
            server_name: Specific server name (not used in current implementation,
                        MultiServerMCPClient returns all tools)
            
        Returns:
            List of LangChain-compatible tools from all MCP servers
        """
        if not self._initialized:
            logger.warning("MCPClientManager not initialized, returning empty tools list")
            return []
        
        if self._tools_cache is None:
            logger.warning("No tools loaded from MCP servers")
            return []
            
        return self._tools_cache
        
    async def refresh_tools(self) -> List[Any]:
        """
        Refresh tools from MCP servers (re-discover).
        
        Returns:
            Updated list of LangChain-compatible tools
        """
        if not self._initialized or self._client is None:
            logger.warning("Cannot refresh tools - client not initialized")
            return []
        
        try:
            logger.info("Refreshing tools from MCP servers...")
            self._tools_cache = await self._client.get_tools()
            logger.info(f"Refreshed {len(self._tools_cache)} tools from MCP servers")
            return self._tools_cache
        except Exception as e:
            logger.error(f"Failed to refresh MCP tools: {e}", exc_info=True)
            return self._tools_cache or []
        
    async def close(self):
        """Close all MCP server connections."""
        if self._client is not None:
            logger.info("Closing MCP client connections")
            # MultiServerMCPClient handles cleanup internally
            self._client = None
        
        self._tools_cache = None
        self._initialized = False


# === SINGLETON PATTERN ===
# We use a singleton to ensure only ONE MCP client manager exists across the entire app.
# This prevents:
# 1. Multiple connections to the same MCP servers (wasteful)
# 2. Tool cache inconsistencies (different instances with different cached tools)
# 3. Race conditions during initialization
#
# Usage:
#   manager = get_mcp_manager()  # Always returns the same instance
#   await manager.initialize(...)  # Only needs to be called once
#   tools = await manager.get_tools()  # Uses cached tools
_mcp_manager: Optional[MCPClientManager] = None


def get_mcp_manager() -> MCPClientManager:
    """
    Get the global singleton MCP client manager instance.
    
    This function implements the singleton pattern - it always returns the same
    MCPClientManager instance throughout the application lifecycle. This ensures
    we maintain a single connection pool to MCP servers and consistent tool caching.
    
    Note: The returned manager is NOT initialized. You must call initialize() 
          with server configs before calling get_tools().
    
    Returns:
        MCPClientManager: The global singleton instance (uninitialized on first call)
        
    Example:
        >>> manager = get_mcp_manager()
        >>> await manager.initialize({"server1": {...}})
        >>> tools = await manager.get_tools()
    """
    global _mcp_manager
    
    if _mcp_manager is None:
        _mcp_manager = MCPClientManager()
        
    return _mcp_manager
