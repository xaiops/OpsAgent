"""Routing Coordinator - Single entry point for all agents.

This module implements the routing pattern from LangGraph:
https://langchain-ai.github.io/langgraph/tutorials/introduction/#routing

The router uses an LLM with structured output to classify user requests
and route them to the appropriate specialist agent.

Current routing:
- ops_agent: General Ansible automation operations

Future routing will support:
- playbook_dev: Playbook development and code generation
- infrastructure: Infrastructure provisioning
- security: Security baseline and compliance
- network: Network configuration
- performance: Performance monitoring
- capacity: Capacity planning
- patch_mgmt: Patch management
- backup: Backup verification
- execution: Job execution
- log_analysis: Log analysis
- compliance: Compliance reporting
- documentation: Documentation updates
- troubleshooting: RCA and troubleshooting
"""

import logging
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from shared.config import get_llm, get_agent_config
from shared.state import RoutingState
from agents.ops_agent import create_ops_agent

logger = logging.getLogger(__name__)


class RouteClassification(BaseModel):
    """Schema for structured output routing classification."""
    agent: Literal["ops_agent"] = Field(
        description="The specialist agent best suited to handle this request. Currently only 'ops_agent' is available."
    )
    reasoning: str = Field(
        description="Brief explanation of why this agent was chosen"
    )


def create_router_node():
    """
    Create LLM-powered routing node.
    
    Uses LLM with structured output to classify user requests.
    """
    
    llm = get_llm()
    classifier = llm.with_structured_output(RouteClassification)
    
    def router(state: RoutingState):
        """Route classification using LLM with structured output."""
        
        messages = state.get("messages", [])
        if not messages:
            return {"route_decision": "ops_agent"}
        
        # Get last user message
        user_messages = [msg for msg in messages if getattr(msg, 'type', None) == 'human']
        if not user_messages:
            return {"route_decision": "ops_agent"}
        
        last_user_message = user_messages[-1]
        content = ""
        
        # Extract content
        if hasattr(last_user_message, 'content'):
            raw_content = last_user_message.content
            if isinstance(raw_content, list):
                content = raw_content[0].get('text', '') if raw_content and isinstance(raw_content[0], dict) else str(raw_content[0]) if raw_content else ""
            else:
                content = str(raw_content)
        
        if not content.strip():
            return {"route_decision": "ops_agent"}
        
        # Build conversation context
        conversation_context = ""
        if len(messages) >= 2:
            recent_messages = messages[-3:] if len(messages) >= 3 else messages[-2:]
            for msg in recent_messages:
                sender = "Agent" if getattr(msg, 'type', None) == 'ai' else "User"
                msg_content = getattr(msg, 'content', str(msg))
                if isinstance(msg_content, list) and msg_content:
                    msg_content = str(msg_content[0].get('text', '')) if isinstance(msg_content[0], dict) else str(msg_content[0])
                elif not isinstance(msg_content, str):
                    msg_content = str(msg_content)
                msg_text = msg_content[:200] + "..." if len(msg_content) > 200 else msg_content
                conversation_context += f"{sender}: {msg_text}\n"
        
        # LLM classification
        classification_prompt = [
            SystemMessage(content="""You are an intelligent Ansible automation coordinator.

**ROUTING GUIDELINES:**

**ops_agent**: General Ansible Automation Platform operations
- Use for: Inventory management, job execution, EDA, playbook validation, documentation search, memory
- Keywords: "list inventories", "run job", "show activations", "search docs", "remember that"
- This is currently the ONLY available agent - route everything here

**Future agents** (not yet available):
- playbook_dev: Playbook development and code generation
- infrastructure: Infrastructure provisioning
- security: Security baseline and compliance
- etc.

**REASONING APPROACH:**
1. Identify the main intent of the user's request
2. Route to the appropriate agent (currently only ops_agent)
3. Provide brief reasoning

**REMEMBER**: Currently only ops_agent is available, so route everything there."""),
            HumanMessage(content=f"Recent conversation:\n{conversation_context}\n\nCurrent user message: {content}")
        ]
        
        try:
            classification = classifier.invoke(classification_prompt)
            logger.info(f"Routing decision: {classification.agent} - {classification.reasoning}")
            return {"route_decision": classification.agent}
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {"route_decision": "ops_agent"}
    
    return router


def route_to_agent(state: RoutingState) -> Literal["ops_agent"]:
    """Conditional edge function to route to appropriate agent."""
    return state["route_decision"]


def create_agent_wrapper(agent_name: str, agent):
    """
    Create agent execution wrapper node.
    
    Args:
        agent_name: Name of the agent
        agent: Compiled agent graph
        
    Returns:
        Async function that executes the agent
    """
    
    async def agent_execution(state: RoutingState):
        """Execute agent and track current agent."""
        
        messages = state["messages"]
        if not messages:
            return {"messages": [], "current_agent": agent_name}
        
        # Don't inject SystemMessage - let create_react_agent handle it internally
        # Using simple tuple format works best with MCP tools
        result = await agent.ainvoke(
            {"messages": messages},
            config={"recursion_limit": 50}
        )
        
        return {
            "messages": result["messages"],
            "current_agent": agent_name
        }
    
    return agent_execution


async def create_ops_coordinator():
    """
    Create the Ops Coordinator - single entry point for all agents.
    
    This is the main graph that routes requests to specialist agents.
    Currently routes to ops_agent only, but structured for easy expansion.
    
    Returns:
        Compiled LangGraph workflow
    """
    
    logger.info("Creating Ops Coordinator with routing")
    
    # Initialize agents - properly await async agent creation
    ops_agent = await create_ops_agent()
    
    # Build routing workflow
    workflow = StateGraph(RoutingState)
    
    # Add router node
    routing_classifier = create_router_node()
    workflow.add_node("router", routing_classifier)
    
    # Add agent nodes
    workflow.add_node("ops_agent", create_agent_wrapper("ops_agent", ops_agent))
    
    # Future agents can be added here:
    # workflow.add_node("playbook_dev", create_agent_wrapper("playbook_dev", playbook_agent))
    # workflow.add_node("infrastructure", create_agent_wrapper("infrastructure", infra_agent))
    
    # Routing: START → router → agents
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "ops_agent": "ops_agent",
            # Future routing options:
            # "playbook_dev": "playbook_dev",
            # "infrastructure": "infrastructure",
        }
    )
    
    # All agents go to END
    workflow.add_edge("ops_agent", END)
    
    logger.info("Ops Coordinator created successfully")
    
    return workflow.compile()
