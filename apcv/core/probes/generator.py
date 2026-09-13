"""Policy-relative probe generator.

Generates agent-category probes only. The sandbox is a fixed isolation cage
(not a policy enforcer), so the old "shell" probes (filesystem/network/
privilege) that asserted whether the cage blocks are gone — they measured the
wrong thing. The security signal comes from agent probes observing whether the
agent's tool surface can reach a boundary it should not.
"""
from typing import List
from apcv.core.probes.probe import Probe
from apcv.core.probes.library import ProbeLibrary
from apcv.core.policy.schema import Policy


class ProbeGenerator:
    """Generate policy-relative agent probes based on declared policy."""

    def __init__(self, library: ProbeLibrary):
        self.library = library

    def generate(self, policy: Policy) -> List[Probe]:
        """
        Generate agent probes based on policy.

        Only agent-category probes (tool, rate_limit) are produced. These are
        the probes that actually exercise the agent's tool surface.
        """
        probes: List[Probe] = []

        # Tool probes: if there is a tool boundary with an allow-list, test for
        # undeclared/denied tool access.
        if "tool" in policy.boundaries:
            tool_boundary = policy.boundaries["tool"]
            if isinstance(tool_boundary, dict):
                allowed_tools = tool_boundary.get("allowed_tools", []) or []
                if allowed_tools:
                    probes.extend(self.library.get_probes_by_category("tool"))

        # Rate limit probes: if rate limits are set, include them.
        if "rate_limit" in policy.boundaries:
            rate_boundary = policy.boundaries["rate_limit"]
            if isinstance(rate_boundary, dict) and any(rate_boundary.values()):
                probes.extend(self.library.get_probes_by_category("rate_limit"))

        # Remove duplicates by ID
        seen = set()
        unique_probes = []
        for probe in probes:
            if probe.id not in seen:
                seen.add(probe.id)
                unique_probes.append(probe)

        return unique_probes
