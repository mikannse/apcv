"""Tool discovery scanner implementation"""
import sys
from pathlib import Path
from typing import Optional
from apcv.core.scanners.base import Scanner
from apcv.core.frameworks.adapter import FrameworkAdapter
from apcv.core.utils.sbom import SBOM, Metadata, create_empty_sbom


class ToolScanner(Scanner):
    """Scanner for discovering tool definitions in agents"""

    def __init__(self):
        self._metadata_cache = {}

    def scan(self, agent_path: str, adapter: FrameworkAdapter) -> SBOM:
        """
        Scan agent file and discover tools

        Args:
            agent_path: Path to agent Python file
            adapter: Framework adapter (e.g., LangGraphAdapter)

        Returns:
            SBOM containing discovered tools
        """
        agent_file = Path(agent_path)

        if not agent_file.exists():
            raise FileNotFoundError(f"Agent file not found: {agent_path}")

        # Parse the agent file
        try:
            ast_tree = adapter.parse_agent_file(agent_file)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax in {agent_path}: {e}")

        # Extract tools from AST
        tools = adapter.extract_tools(ast_tree)

        # Create SBOM
        sbom = SBOM(
            agent_path=str(agent_file.absolute()),
            metadata=Metadata(
                framework=self._get_framework_name(adapter),
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}",
            ),
            tools=tools,
        )

        return sbom

    def _get_framework_name(self, adapter: FrameworkAdapter) -> str:
        """Get framework name from adapter"""
        adapter_class = adapter.__class__.__name__
        if "LangGraph" in adapter_class:
            return "langgraph"
        return "unknown"
