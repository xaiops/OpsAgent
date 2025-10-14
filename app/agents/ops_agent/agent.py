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
    
    === HOW THIS WORKS ===
    1. Check if MCP is enabled in config.yaml
    2. Get the singleton MCPClientManager instance
    3. Initialize it with server configs (URLs, transport type, etc.)
    4. MCPClientManager connects to MCP servers via HTTP
    5. MCP servers return their available tools in MCP protocol format
    6. langchain-mcp-adapters converts them to LangChain BaseTool objects
    7. We add agent-side tools (memory) that aren't provided by MCP
    8. Return complete tool list to create_react_agent()
    
    === ARCHITECTURE ===
    - MCP enabled & working: 46 MCP tools + 1 memory tool = 47 total
    - MCP disabled/failed: 1 memory tool only
    
    === WHY DYNAMIC? ===
    With dynamic tool loading, we don't need to hardcode Ansible tools.
    The MCP server manages the tools, and they're discovered at runtime.
    Benefits:
    - Add new tools to MCP server without changing agent code
    - Version tools independently of the agent
    - Reuse the same agent with different MCP servers
    
    Official pattern: https://langchain-ai.github.io/langgraph/how-tos/mcp/
    
    Returns:
        List[BaseTool]: LangChain tools ready for ReAct agent use
    """
    config = get_agent_config()
    tools = []
    mcp_loaded = False
    
    # === STEP 1: Load MCP tools if enabled ===
    if config.mcp.enabled:
        logger.info("MCP is enabled - loading tools from MCP servers...")
        try:
            # Get the singleton MCP manager (see mcp_integration/client.py)
            mcp_manager = get_mcp_manager()
            
            # Convert Pydantic config objects to plain dicts for MCP client
            # This format matches what MultiServerMCPClient expects
            server_configs = {}
            for server_name, server_config in config.mcp.servers.items():
                server_configs[server_name] = {
                    "name": server_config.name,
                    "url": server_config.url,  # e.g., "http://mcp-server:9005/mcp"
                    "transport": server_config.transport,  # "streamable_http" or "stdio"
                    "timeout": server_config.timeout,
                    "enabled": server_config.enabled,
                }
            
            # Connect to MCP servers and discover tools
            # This is async because it makes HTTP calls to remote servers
            await mcp_manager.initialize(server_configs)
            
            # Get the discovered tools (already converted to LangChain BaseTool format)
            mcp_tools = await mcp_manager.get_tools()
            
            if mcp_tools:
                tools.extend(mcp_tools)
                mcp_loaded = True
                logger.info(f"✅ Loaded {len(mcp_tools)} tools from MCP servers")
                logger.info("   Using MCP tools exclusively (not loading hardcoded tools)")
            else:
                logger.warning("⚠️  No tools loaded from MCP servers")
                
        except Exception as e:
            logger.error(f"❌ Failed to load MCP tools: {e}", exc_info=True)
            logger.warning("   Note: Agent will continue with agent-side tools only")
    else:
        logger.info("MCP is disabled in config - skipping MCP tool loading")
    
    # === STEP 2: Always add agent-side tools ===
    # These tools run locally in the agent (not via MCP):
    # - upsert_memory: Store user preferences and context
    # Agent-side tools are always included regardless of MCP status
    tools.extend(ALL_TOOLS)
    logger.info(f"Added {len(ALL_TOOLS)} agent-side tool(s) (memory management)")
    
    logger.info(f"Total tools available: {len(tools)}")
    
    return tools


async def create_ops_agent():
    """
    Create the Ops Agent using LangGraph's ReAct pattern with MCP tool integration.
    
    === WHAT IS REACT? ===
    ReAct = Reasoning + Acting
    The LLM alternates between:
    1. Reasoning: Think about what to do next
    2. Acting: Call a tool to get information
    3. Observing: See the tool result
    4. Repeat until task is complete
    
    === HOW MCP TOOLS WORK WITH REACT ===
    1. We load tools from MCP servers (via _load_tools_async)
    2. Pass tools to create_react_agent() along with the LLM
    3. LLM receives tool schemas (name, description, parameters)
    4. When user asks a question, LLM decides which tool to call
    5. LangGraph executes the tool call (HTTP request to MCP server)
    6. Tool result comes back to the LLM
    7. LLM uses result to formulate final answer
    
    === EXAMPLE FLOW ===
    User: "List all Ansible inventories"
    1. LLM thinks: "I need to call list_inventories tool"
    2. LangGraph sends tool call to MCP server via HTTP
    3. MCP server executes tool and returns JSON data
    4. LLM receives: [{"id": 1, "name": "Demo Inventory"}]
    5. LLM formats response: "Here are the inventories: Demo Inventory"
    
    Benefits of create_react_agent:
    - Automatic tool calling and execution loop
    - Built-in error handling and retry logic
    - The agent can see tool errors and adjust its strategy
    - Minimal prompt engineering needed (works best with simple prompts)
    - Standard ReAct pattern used across LangGraph
    
    Official docs:
    - ReAct: https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/
    - MCP: https://langchain-ai.github.io/langgraph/how-tos/mcp/
    
    Returns:
        CompiledStateGraph: Compiled ReAct agent ready for execution
    """
    
    # === STEP 1: Get LLM with tool calling support ===
    # The LLM must support function calling (OpenAI-compatible API)
    llm = get_llm()
    
    # === STEP 2: Get configuration ===
    config = get_agent_config()
    
    # === STEP 3: Get minimal system prompt ===
    # Note: create_react_agent works best with minimal prompts
    # Too much detail can confuse the tool calling logic
    system_prompt = config.prompts.system_prompt
    
    # === STEP 4: Load tools from MCP servers ===
    # This is the key step - we dynamically discover tools at runtime
    logger.info("Loading tools for OpsAgent...")
    tools = await _load_tools_async()  # Returns 46 MCP tools + 1 memory tool
    
    logger.info(f"Creating OpsAgent (ReAct) with {len(tools)} tools")
    logger.info(f"Tool names: {[getattr(t, 'name', t.__class__.__name__) for t in tools]}")
    
    # === STEP 5: Create ReAct agent ===
    # create_react_agent() is LangGraph's prebuilt function that creates
    # a complete agent graph with tool calling built in.
    #
    # This automatically creates:
    # - Agent node: Calls LLM with tool schemas and conversation history
    # - Tools node: Executes whichever tool the LLM selected
    # - Conditional edges: Routes between agent → tools → agent in a loop
    # - Error handling: Tool errors are shown to LLM so it can retry/adjust
    #
    # Key parameters:
    # - model: The LLM with tool calling support (must support function calling)
    # - tools: List of LangChain BaseTool objects (from MCP + agent-side)
    # - checkpointer: MemorySaver enables conversation memory across turns
    #
    # Note: We don't pass state_modifier or system prompt here.
    # With create_react_agent, minimal prompts work best when using tuple format.
    # The system prompt is injected at the coordinator level (see routing/coordinator.py)
    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=MemorySaver(),
    )
    
    logger.info("✅ OpsAgent (ReAct) created successfully")
    logger.info(f"   Agent can now use {len(tools)} tools via MCP + local execution")
    
    return agent
