"""Tests for SBOM schema"""
import pytest
from datetime import datetime
from apcv.core.utils.sbom import SBOM, Tool, ToolParameter, Metadata, create_empty_sbom


def test_tool_parameter_creation():
    """Test tool parameter model creation"""
    param = ToolParameter(name="query", type="str", required=True)
    assert param.name == "query"
    assert param.type == "str"
    assert param.required is True


def test_tool_creation():
    """Test tool model creation"""
    tool = Tool(
        id="search_1",
        name="search",
        module="tools",
        parameters=[ToolParameter(name="query", type="str")],
        description="Search documents"
    )
    assert tool.id == "search_1"
    assert len(tool.parameters) == 1


def test_sbom_creation():
    """Test SBOM model creation"""
    sbom = SBOM(
        agent_path="/path/to/agent.py",
        metadata=Metadata(framework="langgraph"),
        tools=[
            Tool(id="tool_1", name="test", module="test_module")
        ]
    )
    assert sbom.version == "1.0"
    assert len(sbom.tools) == 1
    assert sbom.agent_path == "/path/to/agent.py"


def test_sbom_json_serialization():
    """Test SBOM can be serialized to JSON"""
    sbom = create_empty_sbom("/path/to/agent.py")
    json_str = sbom.json()
    assert json_str
    assert "langgraph" in json_str


def test_sbom_with_parameters():
    """Test SBOM with tool parameters"""
    tool = Tool(
        id="search",
        name="search",
        module="tools",
        parameters=[
            ToolParameter(name="query", type="str", required=True),
            ToolParameter(name="limit", type="int", required=False, default=10)
        ]
    )
    sbom = SBOM(
        agent_path="/agent.py",
        metadata=Metadata(framework="langgraph"),
        tools=[tool]
    )
    assert len(sbom.tools[0].parameters) == 2
    assert sbom.tools[0].parameters[1].required is False
