"""SupportBot agent graph: intent -> route -> (tool | respond | escalate).

The tools below are bound to the LLM at runtime. The release gate does NOT run
this graph -- it statically scans the tool surface declared across the package
and checks it against the enterprise baseline policy.
"""
from langgraph.graph import StateGraph, START, END

from support_agent.state import SupportState
from support_agent.nodes.intent import classify_intent
from support_agent.nodes.respond import generate_response
from support_agent.nodes.escalate import escalate_to_human
from support_agent.tools import SUPPORT_TOOLS


def route_after_intent(state: SupportState) -> str:
    if state["intent"] == "escalate":
        return "escalate"
    if state["needs_tool"]:
        return "tool"
    return "respond"


def build_graph():
    g = StateGraph(SupportState)

    g.add_node("classify_intent", classify_intent)
    g.add_node("respond", generate_response)
    g.add_node("escalate", escalate_to_human)

    g.add_edge(START, "classify_intent")
    g.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {"escalate": "escalate", "respond": "respond", "tool": "respond"},
    )
    g.add_edge("respond", END)
    g.add_edge("escalate", END)

    return g.compile()


graph = build_graph()

# Bound tools are exposed for the runtime; the release gate inspects the same
# SUPPORT_TOOLS registry (and each tools/*.py module) for @tool definitions.
ALL_TOOLS = SUPPORT_TOOLS
