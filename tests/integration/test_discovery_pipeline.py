"""Integration tests for discovery pipeline"""
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from apcv.core.scanners.tool_scanner import ToolScanner
from apcv.core.frameworks.langgraph_adapter import LangGraphAdapter
import json


def test_discovery_end_to_end():
    """Test full discovery pipeline with real agent"""
    agent_code = '''
from langraph import tool

@tool
def search(query: str) -> str:
    """Search documents"""
    return f"Results for {query}"

@tool
def get_issue(issue_id: int) -> dict:
    """Get GitHub issue"""
    return {"id": issue_id}
'''

    with TemporaryDirectory() as tmpdir:
        agent_path = Path(tmpdir) / "agent.py"
        agent_path.write_text(agent_code)

        adapter = LangGraphAdapter()
        scanner = ToolScanner()

        sbom = scanner.scan(str(agent_path), adapter)

        assert sbom.metadata.framework == "langgraph"
        assert len(sbom.tools) == 2
        assert sbom.tools[0].name == "search"
        assert sbom.tools[1].name == "get_issue"


def test_discovery_with_complex_types():
    """Test discovery with complex parameter types"""
    agent_code = '''
from typing import List, Dict, Optional
from langraph import tool

@tool
def process(items: List[str], config: Dict[str, int], tags: Optional[str] = None) -> bool:
    """Process items"""
    return True
'''

    with TemporaryDirectory() as tmpdir:
        agent_path = Path(tmpdir) / "agent.py"
        agent_path.write_text(agent_code)

        adapter = LangGraphAdapter()
        scanner = ToolScanner()

        sbom = scanner.scan(str(agent_path), adapter)

        assert len(sbom.tools) == 1
        assert len(sbom.tools[0].parameters) == 3
        assert "List" in sbom.tools[0].parameters[0].type
