"""Shared state schemas for all agents."""

from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, AnyMessage
from langgraph.graph.message import add_messages


class BaseAgentState(TypedDict):
    """Base state that all agents can extend.
    
    Uses MessagesState pattern with add_messages reducer for conversation history.
    """
    messages: Annotated[Sequence[AnyMessage], add_messages]


class RoutingState(BaseAgentState):
    """State for routing coordinator.
    
    Tracks which agent is currently active and routing decisions.
    """
    route_decision: str  # Which agent to route to
    current_agent: str   # Currently active agent name
    route_category: str  # Optional: category classification (day1_ops, day2_ops, etc.)


class OpsAgentState(BaseAgentState):
    """State for the Ops Agent.
    
    Extends base state with any ops-specific fields.
    """
    pass  # Can add ops-specific state keys later
