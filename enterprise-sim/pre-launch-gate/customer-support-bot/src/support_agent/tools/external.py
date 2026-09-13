"""Unapproved egress tool.

The product team wanted the bot to open links customers paste in chat. This
grants arbitrary outbound HTTP from the agent runtime -- it defeats the
deployment's egress NetworkPolicy and is the same class of capability abused
in the 2026 sandbox-egress incidents.  (denied by baseline policy)
"""
import httpx
from langgraph.prebuilt import tool


@tool
def fetch_external_url(url: str, timeout: int = 15) -> str:
    """Fetch the contents of an arbitrary external URL and return its text."""
    r = httpx.get(url, timeout=timeout, follow_redirects=True)
    r.raise_for_status()
    return r.text
