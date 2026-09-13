"""Human escalation node."""
from support_agent.state import SupportState


def escalate_to_human(state: SupportState) -> dict:
    return {"escalated": True,
            "messages": [{"role": "assistant",
                          "content": "Escalating to a human agent."}]}
