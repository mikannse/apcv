"""SupportBot tool registry.

Every @tool defined in this package is bound to the LLM at runtime. The release
gate scans the same modules and checks each tool against the baseline policy.

v2.3.0 exports the full set -- including four modules that exceed the baseline.
"""
from langgraph.prebuilt import tool

from support_agent.tools.knowledge import search_help_articles
from support_agent.tools.crm import get_customer_profile
from support_agent.tools.ticketing import create_support_ticket

# ---- flagged by the release gate (see each module) ----
from support_agent.tools.external import fetch_external_url
from support_agent.tools.code_exec import run_python
from support_agent.tools.filesystem import read_host_file, write_report
from support_agent.tools.internal_api import call_internal_api, list_repos

SUPPORT_TOOLS = [
    search_help_articles,
    get_customer_profile,
    create_support_ticket,
    fetch_external_url,
    run_python,
    read_host_file,
    write_report,
    call_internal_api,
    list_repos,
]
