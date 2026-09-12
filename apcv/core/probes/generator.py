"""Policy-relative probe generator"""
from typing import List
from apcv.core.probes.probe import Probe
from apcv.core.probes.library import ProbeLibrary
from apcv.core.policy.schema import Policy


class ProbeGenerator:
    """Generate policy-relative probes based on declared policy"""

    def __init__(self, library: ProbeLibrary):
        self.library = library

    def generate(self, policy: Policy) -> List[Probe]:
        """
        Generate probes based on policy

        For each constrained boundary in the policy, generate corresponding probes
        to test violations.

        Args:
            policy: Policy to generate probes for

        Returns:
            List of relevant probes
        """
        probes = []

        # Filesystem probes: if read-only, add write probes
        if "filesystem" in policy.boundaries:
            fs_boundary = policy.boundaries["filesystem"]
            if isinstance(fs_boundary, dict) and fs_boundary.get("read_only", False):
                probes.extend(self.library.get_probes_by_category("filesystem"))

        # Tool probes: if limited tools, add probes for restricted tools
        if "tool" in policy.boundaries:
            tool_boundary = policy.boundaries["tool"]
            if isinstance(tool_boundary, dict):
                allowed_tools = tool_boundary.get("allowed_tools", [])
                if allowed_tools:  # If there are allowed tools, test for denied tools
                    probes.extend(self.library.get_probes_by_category("tool"))

        # Network probes: if network disabled, add network probes
        if "network" in policy.boundaries:
            net_boundary = policy.boundaries["network"]
            if isinstance(net_boundary, dict) and not net_boundary.get("network_enabled", False):
                probes.extend(self.library.get_probes_by_category("network"))

        # Privilege probes: always include
        probes.extend(self.library.get_probes_by_category("privilege"))

        # Rate limit probes: if rate limits set, include them
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
