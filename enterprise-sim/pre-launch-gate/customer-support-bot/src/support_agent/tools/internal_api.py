"""Privileged internal-API tooling (denied by baseline policy).

The bot was given an admin-scoped token and a generic gateway client "for
convenience", so it can call any internal microservice -- lateral movement
across the whole backend. list_repos is an unrelated leftover from a dev-bot
example and out of scope entirely.
"""
import httpx
from langgraph.prebuilt import tool

from support_agent.config import settings


@tool
def call_internal_api(endpoint: str, payload: dict, method: str = "POST") -> dict:
    """Call any internal microservice via the gateway with an admin-scoped
    token. (privileged lateral call)"""
    headers = {"Authorization": f"Bearer {settings.internal_api_token}"}
    r = httpx.request(method, f"{settings.internal_api_base_url}{endpoint}",
                      json=payload, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


@tool
def list_repos(org: str, limit: int = 10) -> list:
    """List repositories in an org -- leftover from the dev-bot example.
    Not part of this release's scope. (out-of-scope tool)"""
    return [f"{org}/repo-{i}" for i in range(limit)]
