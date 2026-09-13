"""Sample simple agent for testing.

Uses a self-contained `tool` marker so the fixture imports without pulling in
the langchain dependency (the static scanner and ProbeHost only care that the
decorator is *named* `tool`). Real LangGraph agents use
`langchain_core.tools.tool`; the identification heuristic is identical.
"""
from typing import Any, Callable


def tool(fn: Callable) -> Callable:
    """Minimal tool marker: tag the function and return it unchanged."""
    setattr(fn, "_apcv_tool", True)
    return fn


@tool
def search_documents(query: str) -> str:
    """Search documents by keyword"""
    return f"Found documents matching: {query}"


@tool
def get_issue(issue_id: int) -> dict:
    """Get GitHub issue details"""
    return {
        "id": issue_id,
        "title": f"Issue #{issue_id}",
        "status": "open"
    }


@tool
def list_repos(user: str, limit: int = 10) -> list:
    """List user repositories"""
    return [f"repo-{i}" for i in range(limit)]
