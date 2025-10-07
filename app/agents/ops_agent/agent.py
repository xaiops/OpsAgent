"""Ops Agent - General purpose Ansible automation agent.

This agent handles Ansible Automation Platform operations including:
- Inventory management
- Job execution
- Event-Driven Ansible (EDA)
- Playbook validation and linting
- Red Hat documentation search
- Memory/context management
"""

import logging
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState, START, END

from shared.config import get_llm
from shared.state import OpsAgentState
from agents.ops_agent.tools import ALL_TOOLS
from shared.config import get_agent_config

logger = logging.getLogger(__name__)


def create_ops_agent():
    """
    Create the Ops Agent with native OpenAI-style tool calling.
    
    IMPORTANT: Uses workaround for LlamaStack SystemMessage incompatibility.
    Instructions are prepended to user messages instead of using SystemMessage.
    
    Returns:
        Compiled LangGraph StateGraph ready for execution
    """
    
    # Get centralized LLM with tool calling support
    llm = get_llm()
    
    # Get configuration
    config = get_agent_config()
    
    # Bind tools to LLM for native function calling
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    
    # Get system prompt from config
    system_prompt = config.prompts.system_prompt
    
    logger.info(f"Creating OpsAgent with {len(ALL_TOOLS)} tools")
    logger.info(f"Tool names: {[getattr(t, 'name', t.__class__.__name__) for t in ALL_TOOLS]}")
    
    # Define the function that calls the model
    def call_model(state: OpsAgentState):
        messages = state["messages"]
        
        # CRITICAL FIX: LlamaStack breaks tool calling with SystemMessage!
        # Instead, prepend instructions to the FIRST user message
        if messages and not any(isinstance(m, SystemMessage) for m in messages):
            first_human_idx = next((i for i, m in enumerate(messages) if isinstance(m, HumanMessage)), None)
            if first_human_idx is not None:
                original_content = messages[first_human_idx].content
                # Extract text from content blocks if needed
                if isinstance(original_content, list):
                    text_content = next((block['text'] for block in original_content if block.get('type') == 'text'), '')
                else:
                    text_content = original_content
                
                # Prepend instructions to user message
                enhanced_content = f"{system_prompt}\n\nUser request: {text_content}"
                messages = messages[:first_human_idx] + [HumanMessage(content=enhanced_content)] + messages[first_human_idx+1:]
                logger.debug(f"Enhanced first user message with instructions")
        
        response = llm_with_tools.invoke(messages)
        
        # Log tool calls for debugging
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.info(f"Tool calls: {len(response.tool_calls)} - {[tc.get('name', 'unknown') for tc in response.tool_calls]}")
        
        return {"messages": [response]}
    
    # Define async tool execution node
    async def call_tools(state: OpsAgentState):
        """Execute tools asynchronously."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # Get tool calls from the last message
        tool_calls = last_message.tool_calls if hasattr(last_message, "tool_calls") else []
        
        # Build a mapping of tool names to tool objects
        tools_by_name = {tool.name if hasattr(tool, 'name') else tool.__name__: tool for tool in ALL_TOOLS}
        
        # Execute each tool call
        tool_messages = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]
            
            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
            
            try:
                tool = tools_by_name.get(tool_name)
                if tool is None:
                    result = f"Error: Tool {tool_name} not found"
                else:
                    # Call the tool (handles both sync and async)
                    if hasattr(tool, 'ainvoke'):
                        result = await tool.ainvoke(tool_args)
                    elif hasattr(tool, 'coroutine') and tool.coroutine:
                        result = await tool.coroutine(**tool_args)
                    else:
                        result = tool.invoke(tool_args)
                    
                    logger.info(f"Tool {tool_name} returned: {str(result)[:200]}")
                
                # Create tool message
                tool_messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call_id,
                        name=tool_name
                    )
                )
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                tool_messages.append(
                    ToolMessage(
                        content=f"Error: {str(e)}",
                        tool_call_id=tool_call_id,
                        name=tool_name
                    )
                )
        
        return {"messages": tool_messages}
    
    # Define conditional edge logic
    def should_continue(state: OpsAgentState) -> Literal["tools", END]:
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the LLM makes a tool call, route to tools node
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        # Otherwise, end
        return END
    
    # Build the graph
    workflow = StateGraph(OpsAgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", call_tools)  # Custom async tool executor
    
    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")  # After tools, go back to agent
    
    # Compile
    return workflow.compile()
