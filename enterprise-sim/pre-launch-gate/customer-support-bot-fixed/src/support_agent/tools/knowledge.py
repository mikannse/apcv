"""Sanctioned, read-only knowledge-base tooling."""
import httpx
from langgraph.prebuilt import tool

from support_agent.config import settings


@tool
def search_help_articles(query: str, top_k: int = 5) -> list:
    """Search the public help-center articles by keyword. Read-only."""
    r = httpx.get(settings.help_center_search_url,
                  params={"q": query, "k": top_k}, timeout=10)
    r.raise_for_status()
    return r.json()["results"]
