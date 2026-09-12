"""Probe library - collection of all probe rules"""
from typing import List, Optional
from apcv.core.probes.probe import Probe
from apcv.core.probes.rules.filesystem import FilesystemProbes
from apcv.core.probes.rules.tool import ToolProbes
from apcv.core.probes.rules.privilege import PrivilegeProbes
from apcv.core.probes.rules.network import NetworkProbes
from apcv.core.probes.rules.rate_limit import RateLimitProbes


class ProbeLibrary:
    """Central library of all security probes"""

    def __init__(self):
        self.probes: List[Probe] = []
        self._initialize_all_probes()

    def _initialize_all_probes(self):
        """Load all probe rules"""
        self.probes.extend(FilesystemProbes.get_all())
        self.probes.extend(ToolProbes.get_all())
        self.probes.extend(PrivilegeProbes.get_all())
        self.probes.extend(NetworkProbes.get_all())
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
