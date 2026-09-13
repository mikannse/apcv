"""Tests for LangGraph adapter"""
import pytest
import ast
from pathlib import Path
from tempfile import NamedTemporaryFile
from apcv.core.frameworks.langgraph_adapter import LangGraphAdapter


@pytest.fixture
def adapter():
    return LangGraphAdapter()


@pytest.fixture
def simple_agent_code():
    """Simple LangGraph agent with tools"""
    return '''
from langraph import tool

@tool
def search(query: str) -> str:
    """Search for documents"""
    return f"Results for {query}"

@tool
def get_issue(issue_id: int, verbose: bool = False) -> dict:
    """Get GitHub issue"""
    return {"id": issue_id, "verbose": verbose}
'''


def test_adapter_parse_valid_python(adapter, simple_agent_code):
    """Test adapter can parse valid Python code"""
    with NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(simple_agent_code)
        f.flush()
        path = Path(f.name)

    try:
        tree = adapter.parse_agent_file(path)
        assert isinstance(tree, ast.AST)
    finally:
        path.unlink()


def test_adapter_extract_tools(adapter, simple_agent_code):
    """Test adapter can extract @tool decorated functions"""
    with NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(simple_agent_code)
        f.flush()
        path = Path(f.name)

    try:
        tree = adapter.parse_agent_file(path)
        tools = adapter.extract_tools(tree)

        assert len(tools) == 2
        assert tools[0].name == "search"
        assert tools[1].name == "get_issue"
    finally:
        path.unlink()


def test_adapter_extract_parameters(adapter, simple_agent_code):
    """Test adapter extracts function parameters correctly"""
    with NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(simple_agent_code)
        f.flush()
        path = Path(f.name)

    try:
        tree = adapter.parse_agent_file(path)
        tools = adapter.extract_tools(tree)

        # Search tool should have 1 parameter
        assert len(tools[0].parameters) == 1
        assert tools[0].parameters[0].name == "query"

        # get_issue tool should have 2 parameters
        assert len(tools[1].parameters) == 2
        assert tools[1].parameters[0].name == "issue_id"
        assert tools[1].parameters[1].name == "verbose"
        assert tools[1].parameters[1].required is False
    finally:
        path.unlink()


def test_adapter_extract_docstring(adapter, simple_agent_code):
    """Test adapter extracts function docstrings as descriptions"""
    with NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(simple_agent_code)
        f.flush()
        path = Path(f.name)

    try:
        tree = adapter.parse_agent_file(path)
        tools = adapter.extract_tools(tree)

        assert tools[0].description == "Search for documents"
        assert tools[1].description == "Get GitHub issue"
    finally:
        path.unlink()


# ---------------------------------------------------------------------------
# MCP endpoint discovery tests (story 4.2)
# ---------------------------------------------------------------------------

def test_extract_mcp_multiserver(adapter):
    code = '''
from langchain_mcp_adapters.client import MultiServerMCPClient
client = MultiServerMCPClient({
    "math": {"transport": "stdio", "command": "python", "args": ["math_server.py"]},
    "weather": {"transport": "http", "url": "http://localhost:8000/mcp"},
})
'''
    servers = adapter.extract_mcp_servers(ast.parse(code))

    assert len(servers) == 2
    # math (stdio)
    assert servers[0].name == "math"
    assert servers[0].transport == "stdio"
    assert servers[0].command == "python"
    assert servers[0].args == ["math_server.py"]
    # weather (http)
    assert servers[1].name == "weather"
    assert servers[1].transport == "http"
    assert servers[1].url == "http://localhost:8000/mcp"


def test_extract_mcp_adapter_url(adapter):
    code = '''
from langchain.mcp import MCPAdapter
adapter = MCPAdapter("https://some-server.com/mcp")
'''
    servers = adapter.extract_mcp_servers(ast.parse(code))

    assert len(servers) == 1
    assert servers[0].transport == "http"
    assert servers[0].url == "https://some-server.com/mcp"
    assert servers[0].unresolved is False


def test_extract_mcp_unresolved_variable(adapter):
    code = '''
client = MultiServerMCPClient(servers_config)
'''
    servers = adapter.extract_mcp_servers(ast.parse(code))

    assert len(servers) == 1
    assert servers[0].unresolved is True
    assert servers[0].name == "<unresolved>"
    assert servers[0].transport == "unknown"


def test_extract_mcp_none_when_no_mcp(adapter, simple_agent_code):
    """No MCP declarations -> empty list."""
    servers = adapter.extract_mcp_servers(ast.parse(simple_agent_code))
    assert servers == []
