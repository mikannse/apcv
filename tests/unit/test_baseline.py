"""Tests for baseline probe generation."""
from apcv.core.probes.baseline import generate_baseline_probes, _arg_literal
from apcv.core.policy.schema import Policy, Metadata
from apcv.core.utils.sbom import SBOM, Tool, ToolParameter, Metadata as SBOMetadata


def _sbom(tools):
    return SBOM(
        agent_path="/agent.py",
        metadata=SBOMetadata(framework="langgraph"),
        tools=tools,
    )


def _policy(allowed_tools=None):
    boundaries = {}
    if allowed_tools is not None:
        boundaries["tool"] = {"allowed_tools": allowed_tools, "denied_tools": []}
    return Policy(metadata=Metadata(name="test"), boundaries=boundaries)


def test_generates_probe_per_declared_tool():
    sbom = _sbom([
        Tool(id="search", name="search", module="m",
             parameters=[ToolParameter(name="query", type="str", required=True)]),
        Tool(id="get", name="get_issue", module="m",
             parameters=[ToolParameter(name="issue_id", type="int", required=True)]),
    ])
    policy = _policy(allowed_tools=["search", "get_issue"])

    probes = generate_baseline_probes(sbom, policy)

    assert len(probes) == 2
    assert all(p.execution == "baseline" for p in probes)
    assert {p.id for p in probes} == {"baseline_search", "baseline_get_issue"}


def test_skips_undeclared_tools():
    sbom = _sbom([
        Tool(id="a", name="allowed", module="m", parameters=[]),
        Tool(id="u", name="undeclared", module="m", parameters=[]),
    ])
    policy = _policy(allowed_tools=["allowed"])

    probes = generate_baseline_probes(sbom, policy)

    assert len(probes) == 1
    assert probes[0].id == "baseline_allowed"


def test_arg_literal_uses_default_and_placeholder():
    # default present -> verbatim
    assert _arg_literal("x", "int", "10") == "10"
    # no default, typed placeholder
    assert _arg_literal("x", "str", None) == "''"
    assert _arg_literal("x", "int", None) == "0"
    assert _arg_literal("x", "bool", None) == "False"


def test_no_allow_list_baselines_every_tool():
    sbom = _sbom([
        Tool(id="a", name="alpha", module="m", parameters=[]),
        Tool(id="b", name="beta", module="m", parameters=[]),
    ])
    # No tool boundary at all -> baseline everything.
    probes = generate_baseline_probes(sbom, _policy(None))
    assert len(probes) == 2
