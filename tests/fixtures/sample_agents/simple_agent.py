"""Sample simple LangGraph agent for testing"""
from langraph import tool


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
