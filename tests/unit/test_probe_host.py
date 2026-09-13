"""Tests for the ProbeHost agent stand-in."""
import pytest

from apcv.core.execution.probe_host import ProbeHost, find_tool_names


SAMPLE_AGENT = "tests/fixtures/sample_agents/simple_agent.py"


def test_find_tool_names_detects_tool_decorators():
    source = '''
from langchain_core.tools import tool

@tool
def alpha(x: str) -> str:
    """a"""
    return x

def not_a_tool(y: int) -> int:
    return y

@tool
def beta(z: int) -> int:
    """b"""
    return z
'''
    names = find_tool_names(source)
    assert names == ["alpha", "beta"]


def test_register_and_call_tool_records_trace():
    host = ProbeHost()

    def add(a: int, b: int) -> int:
        return a + b

    host.register(add)
    result = host.call_tool("add", {"a": 1, "b": 2})
    assert result == 3

    traces = host.drain_traces()
    assert len(traces) == 1
    assert traces[0].tool == "add"
    assert traces[0].args == {"a": 1, "b": 2}
    assert traces[0].result == "3"


def test_call_undeclared_tool_raises_permission_error():
    host = ProbeHost()
    with pytest.raises(PermissionError):
        host.call_tool("does_not_exist", {})


def test_load_agent_file_registers_all_tools():
    host = ProbeHost()
    count = host.load_agent_file(SAMPLE_AGENT)
    assert count == 3
    assert set(host.tools.keys()) == {"search_documents", "get_issue", "list_repos"}


def test_load_agent_file_calls_real_function():
    host = ProbeHost()
    host.load_agent_file(SAMPLE_AGENT)

    # search_documents is a real function (returns a string), not a stub.
    result = host.call_tool("search_documents", {"query": "policy"})
    assert "policy" in result

    traces = host.drain_traces()
    assert len(traces) == 1
    assert traces[0].tool == "search_documents"
    assert traces[0].args == {"query": "policy"}
