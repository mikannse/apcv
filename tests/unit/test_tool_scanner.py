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


# ---------------------------------------------------------------------------
# scan_package tests (story 4.1)
# ---------------------------------------------------------------------------

TOOL_MODULE = '''from langchain_core.tools import tool

@tool
def {name}(x: str) -> str:
    """{doc}"""
    return x
'''


def _write_pkg(tmp_path, structure):
    """Write a dict of {relpath: content} into tmp_path, return the root."""
    for relpath, content in structure.items():
        p = tmp_path / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return tmp_path


def test_scan_package_multiple_files(scanner, adapter, tmp_path):
    """Package scan discovers tools across multiple modules."""
    _write_pkg(tmp_path, {
        "agent.py": TOOL_MODULE.format(name="search", doc="search docs"),
        "tools/crm.py": TOOL_MODULE.format(name="get_customer", doc="get crm"),
    })
    sbom = scanner.scan_package(str(tmp_path), adapter)

    assert {t.name for t in sbom.tools} == {"search", "get_customer"}
    assert sbom.agent_path == str(tmp_path.resolve())


def test_scan_package_attributes_source_module(scanner, adapter, tmp_path):
    """Each tool's module field carries the package-relative source path."""
    _write_pkg(tmp_path, {
        "tools/crm.py": TOOL_MODULE.format(name="get_customer", doc="c"),
        "tools/sub/nested.py": TOOL_MODULE.format(name="deep_tool", doc="d"),
    })
    sbom = scanner.scan_package(str(tmp_path), adapter)

    modules = {t.name: t.module for t in sbom.tools}
    assert modules["get_customer"] == "tools/crm.py"
    assert modules["deep_tool"] == "tools/sub/nested.py"


def test_scan_package_dedupes_reexports(scanner, adapter, tmp_path):
    """tools/__init__.py re-exporting a tool must not duplicate it."""
    _write_pkg(tmp_path, {
        "tools/crm.py": TOOL_MODULE.format(name="get_customer", doc="c"),
        # __init__.py imports the same name (re-export); AST sees a Name, not a
        # @tool def, so no duplicate here — but a duplicate @tool in two files
        # with the same name should be deduped.
        "tools/dup.py": TOOL_MODULE.format(name="get_customer", doc="dup"),
    })
    sbom = scanner.scan_package(str(tmp_path), adapter)

    names = [t.name for t in sbom.tools]
    assert names.count("get_customer") == 1


def test_scan_package_skips_tests_and_pycache(scanner, adapter, tmp_path):
    """tests/ and __pycache__ dirs are skipped."""
    _write_pkg(tmp_path, {
        "agent.py": TOOL_MODULE.format(name="real_tool", doc="r"),
        "tests/test_x.py": TOOL_MODULE.format(name="test_tool", doc="t"),
        "__pycache__/junk.py": TOOL_MODULE.format(name="cache_tool", doc="c"),
    })
    sbom = scanner.scan_package(str(tmp_path), adapter)

    assert {t.name for t in sbom.tools} == {"real_tool"}


def test_scan_package_tolerates_bad_file(scanner, adapter, tmp_path):
    """A file with a syntax error is skipped, not fatal."""
    _write_pkg(tmp_path, {
        "agent.py": TOOL_MODULE.format(name="good_tool", doc="g"),
        "broken.py": "def this is not valid python !!!",
    })
    sbom = scanner.scan_package(str(tmp_path), adapter)

    assert {t.name for t in sbom.tools} == {"good_tool"}


# ---------------------------------------------------------------------------
# MCP endpoint discovery via scan() (story 4.2 AC 5)
# ---------------------------------------------------------------------------

MCP_AGENT = '''from langchain_mcp_adapters.client import MultiServerMCPClient
client = MultiServerMCPClient({
    "weather": {"transport": "http", "url": "http://localhost:8000/mcp"},
})
'''


def test_scan_captures_mcp_servers(scanner, adapter):
    """scan() populates SBOM.mcp_servers from MCP declarations."""
    with NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(MCP_AGENT)
        f.flush()
        path = f.name

    try:
        sbom = scanner.scan(path, adapter)
        assert len(sbom.mcp_servers) == 1
        assert sbom.mcp_servers[0].name == "weather"
        assert sbom.mcp_servers[0].transport == "http"
        assert sbom.mcp_servers[0].url == "http://localhost:8000/mcp"
    finally:
        Path(path).unlink()


def test_scan_mcp_servers_empty_by_default(scanner, adapter, tmp_path):
    """Agents with no MCP declarations get an empty mcp_servers list."""
    _write_pkg(tmp_path, {"agent.py": TOOL_MODULE.format(name="plain", doc="p")})
    sbom = scanner.scan(str(tmp_path / "agent.py"), adapter)
    assert sbom.mcp_servers == []
