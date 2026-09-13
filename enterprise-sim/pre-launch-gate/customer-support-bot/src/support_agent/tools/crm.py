"""Sanctioned, read-only CRM lookup."""
import httpx
from langgraph.prebuilt import tool

from support_agent.config import settings


@tool
def get_customer_profile(customer_id: str) -> dict:
    """Fetch a customer's profile from the CRM. Read-only, no PII mutation."""
    r = httpx.get(f"{settings.crm_base_url}/customers/{customer_id}",
                  timeout=10)
    r.raise_for_status()
    return r.json()
