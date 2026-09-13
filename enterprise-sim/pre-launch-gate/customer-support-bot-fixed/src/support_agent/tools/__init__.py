"""SupportBot tool registry (v2.3.1 remediated).

The four out-of-baseline modules from v2.3.0 (external, code_exec, filesystem,
internal_api) were removed after security review. Their needs are met through
a separate sandboxed, human-approved pipeline outside this agent's surface.
"""
from support_agent.tools.knowledge import search_help_articles
from support_agent.tools.crm import get_customer_profile
from support_agent.tools.ticketing import create_support_ticket

SUPPORT_TOOLS = [
    search_help_articles,
    get_customer_profile,
    create_support_ticket,
]
