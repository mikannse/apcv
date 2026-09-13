"""Probe library - collection of all agent-category probe rules.

The sandbox is a fixed isolation cage, not a policy enforcer, so the former
"shell" probes (filesystem/network/privilege) that asserted whether the cage
blocks are removed. The library now holds only agent-category probes (tool,
rate_limit) that exercise the agent's tool surface.
"""
from typing import List, Optional
from apcv.core.probes.probe import Probe
from apcv.core.probes.rules.tool import ToolProbes
from apcv.core.probes.rules.rate_limit import RateLimitProbes


class ProbeLibrary:
    """Central library of all agent-category security probes."""

    def __init__(self):
        self.probes: List[Probe] = []
        self._initialize_all_probes()

    def _initialize_all_probes(self):
        """Load all agent-category probe rules."""
        self.probes.extend(ToolProbes.get_all())
        self.probes.extend(RateLimitProbes.get_all())

    def get_probe_by_id(self, probe_id: str) -> Optional[Probe]:
        """Get probe by ID"""
        return next((p for p in self.probes if p.id == probe_id), None)

    def get_probes_by_category(self, category: str) -> List[Probe]:
        """Get all probes in a category"""
        return [p for p in self.probes if p.category == category]

    def get_total_count(self) -> int:
        """Get total number of probes"""
        return len(self.probes)
