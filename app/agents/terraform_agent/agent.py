"""Terraform Agent implementation.

This module creates a specialized Terraform agent with enhanced capabilities
for infrastructure management and deployment workflows.
"""

import logging
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from shared.config import get_llm, get_agent_config
from mcp_integration.client import get_mcp_manager

logger = logging.getLogger(__name__)


async def create_terraform_agent():
    """
    Create a specialized Terraform Cloud agent.
    
    This agent is configured with:
    - All Terraform MCP tools (workspaces, runs, variables, etc.)
    - Specialized prompts for Terraform operations
    - Built-in workflow understanding for RHEL 9 VM deployments
    
    The agent can handle:
    - Workspace management (create, list, configure)
    - Variable management (env vars and terraform vars)
    - Run management (plan, apply, monitor)
    - Complex multi-step workflows like RHEL 9 VM deployment
    
    Returns:
        CompiledStateGraph: Compiled ReAct agent for Terraform operations
    """
    
    logger.info("Creating Terraform Cloud specialized agent...")
    
    # Get LLM
    llm = get_llm()
    
    # Get configuration
    config = get_agent_config()
    
    # Get Terraform tools from MCP
    mcp_manager = get_mcp_manager()
    
    # Initialize MCP manager if not already initialized
    if not mcp_manager._initialized:
        logger.info("Initializing MCP manager for Terraform agent...")
        server_configs = {}
        for srv_name, srv_config in config.mcp.servers.items():
            server_configs[srv_name] = {
                "name": srv_config.name,
                "url": srv_config.url,
                "transport": srv_config.transport,
                "timeout": srv_config.timeout,
                "enabled": srv_config.enabled,
                "headers": srv_config.headers,
            }
        await mcp_manager.initialize(server_configs)
        logger.info("MCP manager initialized")
    
    # Get Terraform-specific tools
    tools = await mcp_manager.get_tools(server_name="terraform")
    
    if not tools:
        logger.warning("No Terraform tools found - agent will have limited capabilities")
    else:
        logger.info(f"Loaded {len(tools)} Terraform tools from MCP server")
        logger.info(f"Available tools: {[tool.name for tool in tools]}")
    
    # Create ReAct agent with Terraform tools
    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=MemorySaver(),
    )
    
    # Store prompt key for coordinator to use
    agent._prompt_key = "terraform_agent"
    
    logger.info("✓ Terraform agent created successfully")
    
    return agent

