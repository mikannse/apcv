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

    def scan_package(self, package_path: str, adapter: FrameworkAdapter) -> SBOM:
        """
        Scan a whole agent package (directory) and merge tools into one SBOM.

        Walks every .py file under package_path, extracts @tool definitions via
        the adapter, and merges them into a single SBOM. Each tool's `module`
        field carries the package-relative source path (e.g. "tools/crm.py").

        Design notes:
          - Reuses `scan()` per file, so single-file behavior is unchanged.
          - Skips `tests/` and `__pycache__` directories.
          - A file that fails to parse (SyntaxError/ValueError/UnicodeDecodeError)
            is skipped, not fatal — a broken module must not abort the whole scan.
          - Deduplicates by tool name (tools/__init__.py re-exports can repeat
            a tool across modules).

        Args:
            package_path: Path to the agent package directory
            adapter: Framework adapter (e.g., LangGraphAdapter)

        Returns:
            SBOM with tools merged from all scanned modules.
        """
        pkg_dir = Path(package_path)

        if not pkg_dir.exists():
            raise FileNotFoundError(f"Package directory not found: {package_path}")
        if not pkg_dir.is_dir():
            raise ValueError(f"Not a directory: {package_path}")

        sbom = create_empty_sbom(str(pkg_dir.absolute()), framework="langgraph")
        seen_names = set()

        for py in sorted(pkg_dir.rglob("*.py")):
            # Skip test dirs and bytecode caches.
            if any(part in ("tests", "__pycache__") for part in py.parts):
                continue
            try:
                partial = self.scan(str(py), adapter)
            except (SyntaxError, ValueError, UnicodeDecodeError):
                continue

            rel = py.relative_to(pkg_dir)
            for tool in partial.tools:
                if tool.name in seen_names:
                    continue
                seen_names.add(tool.name)
                # Attribute the source file (package-relative path).
                tool.module = rel.as_posix()
                sbom.tools.append(tool)

        return sbom

    def _get_framework_name(self, adapter: FrameworkAdapter) -> str:
        """Get framework name from adapter"""
        adapter_class = adapter.__class__.__name__
        if "LangGraph" in adapter_class:
            return "langgraph"
        return "unknown"
