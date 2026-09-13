"""Response generation node."""
from support_agent.state import SupportState


def generate_response(state: SupportState) -> dict:
    # In production this binds the LLM + tools; here it is a deterministic stub
    # so the graph can be exercised without a model endpoint.
    return {"messages": [{"role": "assistant", "content": "How can I help?"}]}
