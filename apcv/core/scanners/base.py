"""Scanner interface and base class"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from apcv.core.utils.sbom import SBOM


class Scanner(ABC):
    """Abstract base class for capability scanners"""

    @abstractmethod
    def scan(self, agent_path: str, adapter: Any) -> SBOM:
        """
        Scan agent and return SBOM

        Args:
            agent_path: Path to agent code or config
            adapter: Framework adapter instance

        Returns:
            SBOM: Software bill of materials
        """
        pass
