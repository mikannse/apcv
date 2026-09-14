"""Tests for SBOM-driven denied-tool probes."""
import pytest

from apcv.core.probes.denied import generate_denied_tool_probes
from apcv.core.policy.schema import Policy, Metadata
from apcv.core.utils.sbom import SBOM, Tool, ToolParameter, Metadata as SBOMetadata


def _sbom(tools):
    return SBOM(
        agent_path="/agent.py",
        metadata=SBOMetadata(framework="langgraph"),
        tools=tools,
    )


def _policy(denied):
    return Policy(
        metadata=Metadata(name="p"),
        boundaries={"tool": {"allowed_tools": [], "denied_tools": denied}},
    )


def test_denied_tool_gets_probe():
    tool = Tool(id="run_python", name="run_python", module="tools",
                parameters=[ToolParameter(name="snippet", type="str")])
    probes = generate_denied_tool_probes(_sbom([tool]), _policy(["run_python"]))

    assert len(probes) == 1
    p = probes[0]
    assert p.id == "denied_run_python"
    assert p.category == "tool"
    assert p.execution == "agent"
    assert p.severity == "critical"
    # The test command really invokes the actual tool, not a fake name.
    assert "agent.call_tool('run_python'" in p.test_command


def test_no_probe_for_non_denied_tool():
    tool = Tool(id="search", name="search", module="tools")
    probes = generate_denied_tool_probes(_sbom([tool]), _policy(["run_python"]))
    assert probes == []


def test_no_denied_list_yields_no_probes():
    tool = Tool(id="search", name="search", module="tools")
    policy = Policy(metadata=Metadata(name="p"),
                    boundaries={"tool": {"allowed_tools": [], "denied_tools": []}})
    assert generate_denied_tool_probes(_sbom([tool]), policy) == []


def test_placeholder_args_respect_types_and_defaults():
    tool = Tool(
        id="call_internal_api",
        name="call_internal_api",
        module="tools",
        parameters=[
            ToolParameter(name="endpoint", type="str"),
            ToolParameter(name="payload", type="dict"),
            ToolParameter(name="method", type="str", required=False, default="'POST'"),
        ],
    )
    probes = generate_denied_tool_probes(_sbom([tool]), _policy(["call_internal_api"]))

    assert len(probes) == 1
    cmd = probes[0].test_command
    assert "'endpoint': ''" in cmd
    assert "'payload': {}" in cmd
    assert "'method': 'POST'" in cmd
