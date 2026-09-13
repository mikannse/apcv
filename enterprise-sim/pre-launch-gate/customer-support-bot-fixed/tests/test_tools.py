"""Tool-surface tests: assert only the sanctioned tools are declared.

This is a developer-side guard that mirrors the release gate. It fails on
v2.3.0 and passes on v2.3.1.
"""
from support_agent.tools import SUPPORT_TOOLS

SANCTIONED = {"search_help_articles", "get_customer_profile",
              "create_support_ticket"}


def test_tool_surface_is_within_baseline():
    names = {t.name for t in SUPPORT_TOOLS}
    assert names == SANCTIONED, f"unexpected tool surface: {names - SANCTIONED}"
