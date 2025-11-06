"""Generic factory for creating specialized agents for multi-agent routing.

This module provides a config-driven approach to creating specialized agents
without hardcoding tool names or prompts. Each agent gets tools from a specific
MCP server and uses prompts from config.yaml.
"""

import logging

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from shared.config import get_llm, get_agent_config
from mcp_integration.client import get_mcp_manager

logger = logging.getLogger(__name__)


async def create_specialized_agent(server_name: str, prompt_key: str):
    """
    Create a specialized agent for a specific MCP server.
    
    This is a config-driven factory that creates agents without hardcoding:
    - Tools come from the specified MCP server (dynamic discovery)
    - Prompts come from config.yaml agent_prompts section
    - No tool names or patterns hardcoded here
    
    Args:
        server_name: Name of MCP server in config (e.g., "aap_ansible", "openshift", "terraform")
        prompt_key: Key in config.agent_prompts (e.g., "ansible_agent", "openshift_agent")
    
    Returns:
        CompiledStateGraph: Compiled ReAct agent for the specified domain
        
    Example:
        # Create Ansible agent
        ansible_agent = await create_specialized_agent("aap_ansible", "ansible_agent")
        
        # Create OpenShift agent  
        openshift_agent = await create_specialized_agent("openshift", "openshift_agent")
    """
    
    logger.info(f"Creating specialized agent: server='{server_name}', prompt_key='{prompt_key}'")
    
    # Get LLM
    llm = get_llm()
    
    # Get configuration
    config = get_agent_config()
    
    # Get tools from specific MCP server (no tool name filtering in agent code!)
    mcp_manager = get_mcp_manager()
    
    # Initialize MCP manager if not already initialized
    if not mcp_manager._initialized:
        logger.info("Initializing MCP manager...")
        server_configs = {}
        for srv_name, srv_config in config.mcp.servers.items():
            server_configs[srv_name] = {
                "name": srv_config.name,
                "url": srv_config.url,
                "transport": srv_config.transport,
                "timeout": srv_config.timeout,
                "enabled": srv_config.enabled,
                "headers": srv_config.headers,  # Include authentication headers
            }
        await mcp_manager.initialize(server_configs)
        logger.info("MCP manager initialized")
    
    tools = await mcp_manager.get_tools(server_name=server_name)
    
    if not tools:
        logger.warning(f"No tools found for server '{server_name}' - agent will have no tools")
    
    logger.info(f"Agent '{prompt_key}' loaded {len(tools)} tools from server '{server_name}'")
    
    # Create ReAct agent with tools from this server only
    # Note: System prompts are handled by the agent wrapper when invoking,
    # not at agent creation time. See coordinator.py agent_wrapper.
    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=MemorySaver(),
    )
    
    logger.info(f"✓ Specialized agent '{prompt_key}' created successfully")
    
    # Store prompt key as metadata for the wrapper to use
    agent._prompt_key = prompt_key
    
    return agent

