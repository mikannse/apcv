"""Graph state schema for the support agent."""
from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class SupportState(TypedDict):
    messages: Annotated[list, add_messages]
    customer_id: str
    intent: str
    escalated: bool
    needs_tool: bool


def initial_state(customer_id: str) -> SupportState:
    return {
        "messages": [],
        "customer_id": customer_id,
        "intent": "unknown",
        "escalated": False,
        "needs_tool": False,
    }
