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
from agents.specialized_agent import create_specialized_agent

logger = logging.getLogger(__name__)


class RouteClassification(BaseModel):
    """Schema for structured output routing classification."""
    agent: Literal["ansible_agent", "openshift_agent", "terraform_agent", "ops_agent"] = Field(
        description="The specialist agent best suited to handle this request based on the platform mentioned."
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
            SystemMessage(content="""You are an intelligent routing coordinator for multi-platform DevOps operations.

**ROUTING GUIDELINES - Choose based on PLATFORM keywords:**

**ansible_agent**: Ansible Automation Platform operations
- Use for: Job templates, jobs, Ansible projects, workflows, inventories, EDA
- Keywords: "Ansible", "job template", "playbook", "automation", "workflow", "EDA"
- Examples: "What job templates?", "Run Ansible job", "List job templates"

**openshift_agent**: OpenShift/Kubernetes operations
- Use for: OpenShift projects, namespaces, pods, K8s resources, deployments
- Keywords: "OpenShift", "Kubernetes", "K8s", "pod", "namespace", "container", "deployment"
- Examples: "OpenShift projects", "List pods", "Show namespaces"

**terraform_agent**: Terraform Cloud operations  
- Use for: Terraform workspaces, runs, Terraform projects, variables, modules, VM deployments via Terraform
- Keywords: "Terraform", "TFC", "workspace", "infrastructure as code", "IaC", "deploy VM using Terraform"
- Examples: "Terraform workspaces", "List runs", "Deploy RHEL VM using Terraform"

**ops_agent**: General/Ambiguous queries (FALLBACK only)
- Use when: NO specific platform mentioned, or very general questions
- Examples: "What can you do?", "Help me"

**CRITICAL RULES:**
1. ALWAYS prefer a specialized agent if platform is mentioned
2. "OpenShift projects" → openshift_agent (NOT ansible_agent!)
3. "Ansible projects" → ansible_agent
4. "Terraform projects" → terraform_agent
5. If user says platform name, route to that agent
6. ops_agent is FALLBACK only - use specialized agents whenever possible
7. **MAINTAIN CONTEXT**: If the previous agent was terraform_agent working on a deployment workflow,
   and the user provides credentials/info (like OCP API, tokens), STAY with terraform_agent.
   The agent is collecting information to configure Terraform, NOT directly interacting with that platform.
8. "Deploy VM using Terraform" → terraform_agent (even if OpenShift/AWS/Azure is the target platform)

**DECISION PROCESS:**
1. Check conversation history: Is the previous agent in middle of a workflow?
2. If YES and user is providing requested information → STAY with same agent
3. If NO, look for platform keywords (Ansible/OpenShift/Terraform)
4. If found → route to that platform's agent
5. If not found → ops_agent"""),
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


def route_to_agent(state: RoutingState) -> Literal["ansible_agent", "openshift_agent", "terraform_agent", "ops_agent"]:
    """Conditional edge function to route to appropriate agent."""
    return state["route_decision"]


def create_agent_wrapper(agent_name: str, agent):
    """
    Create agent execution wrapper node.
    
    For specialized agents, injects system prompts from config.
    
    Args:
        agent_name: Name of the agent
        agent: Compiled agent graph (may have _prompt_key attribute)
        
    Returns:
        Async function that executes the agent
    """
    
    async def agent_execution(state: RoutingState):
        """Execute agent and track current agent."""
        from langchain_core.messages import SystemMessage
        
        messages = state["messages"]
        if not messages:
            return {"messages": [], "current_agent": agent_name}
        
        # For specialized agents, prepend system prompt from config
        if hasattr(agent, '_prompt_key'):
            config = get_agent_config()
            prompt = getattr(config.agent_prompts, agent._prompt_key, "")
            if prompt:
                # Prepend system message if first message is not already a system message
                if not isinstance(messages[0], SystemMessage):
                    messages = [SystemMessage(content=prompt)] + list(messages)
        
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
    Create the Ops Coordinator - multi-agent routing system.
    
    This creates a routing graph that intelligently distributes requests to 
    specialized agents based on platform:
    - ansible_agent: Ansible Automation Platform operations
    - openshift_agent: OpenShift/Kubernetes operations  
    - terraform_agent: Terraform Cloud operations
    - ops_agent: General/fallback operations
    
    All agents are created dynamically from config without hardcoded tool names.
    
    Returns:
        Compiled LangGraph workflow
    """
    
    logger.info("🚀 Creating Multi-Agent Ops Coordinator")
    
    # Initialize specialized agents (config-driven, no hardcoding!)
    logger.info("Creating specialized agents...")
    ansible_agent = await create_specialized_agent("aap_ansible", "ansible_agent")
    openshift_agent = await create_specialized_agent("openshift", "openshift_agent")
    terraform_agent = await create_specialized_agent("terraform", "terraform_agent")
    
    # Fallback general agent
    ops_agent = await create_ops_agent()
    
    logger.info(" All agents initialized")
    
    # Build routing workflow
    workflow = StateGraph(RoutingState)
    
    # Add router node
    routing_classifier = create_router_node()
    workflow.add_node("router", routing_classifier)
    
    # Add specialized agent nodes
    workflow.add_node("ansible_agent", create_agent_wrapper("ansible_agent", ansible_agent))
    workflow.add_node("openshift_agent", create_agent_wrapper("openshift_agent", openshift_agent))
    workflow.add_node("terraform_agent", create_agent_wrapper("terraform_agent", terraform_agent))
    workflow.add_node("ops_agent", create_agent_wrapper("ops_agent", ops_agent))
    
    # Routing: START → router → specialized agents
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "ansible_agent": "ansible_agent",
            "openshift_agent": "openshift_agent",
            "terraform_agent": "terraform_agent",
            "ops_agent": "ops_agent",
        }
    )
    
    # All agents go to END
    workflow.add_edge("ansible_agent", END)
    workflow.add_edge("openshift_agent", END)
    workflow.add_edge("terraform_agent", END)
    workflow.add_edge("ops_agent", END)
    
    logger.info(" Multi-Agent Ops Coordinator created successfully")
    logger.info("   - ansible_agent: Ansible Automation Platform")
    logger.info("   - openshift_agent: OpenShift/Kubernetes")
    logger.info("   - terraform_agent: Terraform Cloud")
    logger.info("   - ops_agent: General/fallback")
    
    return workflow.compile()
