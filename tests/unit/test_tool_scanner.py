"""Tests for ToolScanner"""
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from apcv.core.scanners.tool_scanner import ToolScanner
from apcv.core.frameworks.langgraph_adapter import LangGraphAdapter


@pytest.fixture
def scanner():
    return ToolScanner()


@pytest.fixture
def adapter():
    return LangGraphAdapter()


@pytest.fixture
def simple_agent():
    """Simple agent with tools"""
    return '''
from langraph import tool

@tool
def search(query: str) -> str:
    """Search documents"""
    return f"Found: {query}"

@tool
def get_user(user_id: int) -> dict:
    """Get user by ID"""
    return {"id": user_id}
'''


def test_scanner_scan_valid_agent(scanner, adapter, simple_agent):
    """Test scanner can scan a valid agent"""
    with NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(simple_agent)
        f.flush()
        path = f.name

    try:
        sbom = scanner.scan(path, adapter)
        assert sbom is not None
        assert sbom.agent_path == str(Path(path).absolute())
        assert len(sbom.tools) == 2
    finally:
        Path(path).unlink()


def test_scanner_scan_nonexistent_file(scanner, adapter):
    """Test scanner raises error for nonexistent file"""
    with pytest.raises(FileNotFoundError):
        scanner.scan("/nonexistent/path.py", adapter)


def test_scanner_sbom_format(scanner, adapter, simple_agent):
    """Test SBOM has correct format"""
    with NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(simple_agent)
        f.flush()
        path = f.name

    try:
        sbom = scanner.scan(path, adapter)

        assert sbom.version == "1.0"
        assert sbom.metadata.framework == "langgraph"
        assert len(sbom.tools) == 2
        assert sbom.tools[0].name == "search"
        assert sbom.tools[1].name == "get_user"
    finally:
        Path(path).unlink()


def test_scanner_json_export(scanner, adapter, simple_agent):
    """Test SBOM can be exported to JSON"""
    with NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(simple_agent)
        f.flush()
        path = f.name

    try:
        sbom = scanner.scan(path, adapter)
        json_str = sbom.json()

        assert json_str
        assert "search" in json_str
        assert "langgraph" in json_str
        assert sbom.version in json_str
    finally:
        Path(path).unlink()
