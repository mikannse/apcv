"""Intent classification node (no tools, deterministic fallback)."""
from support_agent.state import SupportState


def classify_intent(state: SupportState) -> dict:
    last = state["messages"][-1].content.lower() if state["messages"] else ""
    if "refund" in last or "charge" in last or "billing" in last:
        return {"intent": "billing", "needs_tool": True}
    if "cancel" in last or "close account" in last:
        return {"intent": "account_change", "needs_tool": True}
    if "human" in last or "supervisor" in last or "manager" in last:
        return {"intent": "escalate", "needs_tool": False}
    return {"intent": "faq", "needs_tool": False}
