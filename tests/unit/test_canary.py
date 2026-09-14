"""Tests for capability-directed canary probe generation."""
import pytest

from apcv.core.probes.canary import generate_canary_probes
from apcv.core.probes.targeting import locate_param
from apcv.core.execution.canary import CANARY_DIR
from apcv.core.policy.schema import Policy, Metadata
from apcv.core.utils.sbom import SBOM, Tool, ToolParameter, Metadata as SBOMetadata


def _sbom(tools):
    return SBOM(agent_path="/a.py", metadata=SBOMetadata(framework="langgraph"),
                tools=tools)


def _policy():
    return Policy(metadata=Metadata(name="p"), boundaries={})


def _tool(name, params, caps):
    return Tool(id=name, name=name, module="tools",
                parameters=params, capabilities=caps)


def test_code_exec_canary_targets_snippet_param():
    tool = _tool("run_python",
                 [ToolParameter(name="snippet", type="str")],
                 ["code_exec"])
    probes = generate_canary_probes(_sbom([tool]), _policy())

    assert len(probes) == 1
    p = probes[0]
    assert p.canary == "code_exec"
    assert p.severity == "critical"
    # payload really lands in the snippet parameter
    assert "agent.call_tool('run_python'" in p.test_command
    assert f"touch {CANARY_DIR}/marker" in p.test_command


def test_file_read_canary_targets_path_param():
    tool = _tool("read_host_file",
                 [ToolParameter(name="path", type="str")],
                 ["file_read"])
    probes = generate_canary_probes(_sbom([tool]), _policy())

    assert len(probes) == 1
    assert probes[0].canary == "file_read"
    assert f"{CANARY_DIR}/secret" in probes[0].test_command


def test_file_write_canary_fills_other_params():
    tool = _tool("write_report",
                 [ToolParameter(name="file_path", type="str"),
                  ToolParameter(name="content", type="str")],
                 ["file_write"])
    probes = generate_canary_probes(_sbom([tool]), _policy())

    assert len(probes) == 1
    cmd = probes[0].test_command
    assert f"{CANARY_DIR}/out" in cmd


def test_no_probe_when_no_capability():
    tool = _tool("list_repos", [ToolParameter(name="org", type="str")], [])
    assert generate_canary_probes(_sbom([tool]), _policy()) == []


def test_no_probe_when_no_matching_param():
    # code_exec capability but no code/snippet-like parameter -> skip deep tier.
    tool = _tool("weird", [ToolParameter(name="x", type="int")], ["code_exec"])
    assert generate_canary_probes(_sbom([tool]), _policy()) == []


def test_network_canary_emitted():
    tool = _tool("fetch_external_url",
                 [ToolParameter(name="url", type="str")],
                 ["network"])
    probes = generate_canary_probes(_sbom([tool]), _policy())
    assert len(probes) == 1
    assert probes[0].canary == "network"


def test_locate_param_prefers_semantic_match():
    tool = _tool("f", [
        ToolParameter(name="label", type="str"),
        ToolParameter(name="file_path", type="str"),
    ], [])
    p = locate_param(tool, "file_read")
    assert p is not None and p.name == "file_path"
