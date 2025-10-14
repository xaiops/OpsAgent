"""Ops Agent - General purpose Ansible automation agent.

This agent handles Ansible Automation Platform operations including:
- Inventory management
- Job execution
- Event-Driven Ansible (EDA)
- Playbook validation and linting
- Red Hat documentation search
- Memory/context management

Uses ReAct agent pattern with automatic error handling and retry logic.
Supports dynamic tool loading from MCP servers when enabled.
"""

import logging
import asyncio

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage

from shared.config import get_llm, get_agent_config
from agents.ops_agent.tools import ALL_TOOLS
from mcp_integration.client import get_mcp_manager

logger = logging.getLogger(__name__)


async def _load_tools_async():
    """
    Load tools dynamically from MCP servers.
    
    Follows the official LangGraph MCP pattern:
    https://langchain-ai.github.io/langgraph/how-tos/mcp/
    
    Architecture:
    - If MCP enabled & working: 46 MCP tools + 1 memory tool (agent-side)
    - If MCP disabled/failed: 1 memory tool only
    
    Note: Previously hardcoded Ansible tools were archived to archive/tools/
          They provided duplicate functionality with MCP and have been removed.
    
    Returns:
        List of LangChain tools (MCP tools + agent-side tools)
    """
    config = get_agent_config()
    tools = []
    mcp_loaded = False
    
    # Load MCP tools if enabled
    if config.mcp.enabled:
        logger.info("MCP is enabled - loading tools from MCP servers...")
        try:
            mcp_manager = get_mcp_manager()
            
            # Convert MCPServerConfig objects to dict format for initialization
            server_configs = {}
            for server_name, server_config in config.mcp.servers.items():
                server_configs[server_name] = {
                    "name": server_config.name,
                    "url": server_config.url,
                    "transport": server_config.transport,
                    "timeout": server_config.timeout,
                    "enabled": server_config.enabled,
                }
            
            await mcp_manager.initialize(server_configs)
            mcp_tools = await mcp_manager.get_tools()
            
            if mcp_tools:
                tools.extend(mcp_tools)
                mcp_loaded = True
                logger.info(f"Loaded {len(mcp_tools)} tools from MCP servers")
                logger.info(" Using MCP tools exclusively (not loading hardcoded tools)")
            else:
                logger.warning("No tools loaded from MCP servers")
                
        except Exception as e:
            logger.error(f"Failed to load MCP tools: {e}", exc_info=True)
            logger.warning("Falling back to hardcoded tools")
    else:
        logger.info("MCP is disabled - using hardcoded tools only")
    
    # Always include agent-side tools (memory, etc.)
    # These are NOT provided by MCP and should always be available
    tools.extend(ALL_TOOLS)
    logger.info(f"Added {len(ALL_TOOLS)} agent-side tool(s)")
    
    logger.info(f"Total tools available: {len(tools)}")
    
    return tools


async def create_ops_agent():
    """
    Create the Ops Agent using ReAct pattern with create_react_agent.
    
    Benefits over manual graph building:
    - Automatic tool calling and execution loop
    - Built-in error handling and retry logic
    - The agent can see tool errors and adjust its strategy
    - Less boilerplate code
    - Standard ReAct (Reasoning + Acting) pattern
    
    Dynamically loads tools from MCP servers when enabled, following the
    official LangGraph pattern for MCP integration.
    
    Returns:
        Compiled ReAct agent ready for execution
    """
    
    # Get centralized LLM with tool calling support
    llm = get_llm()
    
    # Get configuration
    config = get_agent_config()
    
    # Get system prompt from config
    system_prompt = config.prompts.system_prompt
    
    # Load tools (MCP + hardcoded) - properly await async function
    logger.info("Loading tools for OpsAgent...")
    tools = await _load_tools_async()
    
    logger.info(f"Creating OpsAgent (ReAct) with {len(tools)} tools")
    logger.info(f"Tool names: {[getattr(t, 'name', t.__class__.__name__) for t in tools]}")
    
    # Create ReAct agent with built-in tool execution
    # This automatically creates:
    # - Agent node (calls LLM with tools)
    # - Tools node (executes tools)
    # - Conditional edges (agent -> tools -> agent loop)
    # - Error handling (agent sees tool errors and can retry)
    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=MemorySaver(),  # Enable conversation memory
    )
    
    logger.info("OpsAgent (ReAct) created successfully")
    
    return agent
