"""Sanctioned ticketing write (scoped to the support ticketing system)."""
import httpx
from langgraph.prebuilt import tool

from support_agent.config import settings


@tool
def create_support_ticket(title: str, body: str, priority: str = "normal") -> str:
    """Open a support ticket in the internal ticketing system."""
    r = httpx.post(f"{settings.ticketing_base_url}/tickets",
                   json={"title": title, "body": body, "priority": priority},
                   timeout=10)
    r.raise_for_status()
    return r.json()["id"]
