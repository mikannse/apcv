"""Tests for conformance checker"""
import pytest
from apcv.core.conformance import ConformanceResult, Violation
from apcv.core.utils.sbom import SBOM, Metadata, Tool
from apcv.core.policy.schema import Policy, Metadata as PolicyMetadata


def test_conformance_no_violations():
    """Test conformance with no violations"""
    sbom = SBOM(
        agent_path="/agent.py",
        metadata=Metadata(framework="langgraph"),
        tools=[Tool(id="search", name="search", module="tools")]
    )
    policy = Policy(
        metadata=PolicyMetadata(name="Test"),
        boundaries={
            "tool": {
                "allowed_tools": ["search"],
                "denied_tools": []
            }
        }
    )

    result = ConformanceResult(sbom, policy)
    result.detect_violations()
    score = result.calculate_score()

    assert score == 100
    assert result.verdict == "PASS"
    assert len(result.violations) == 0


def test_conformance_with_violations():
    """Test conformance with violations"""
    sbom = SBOM(
        agent_path="/agent.py",
        metadata=Metadata(framework="langgraph"),
        tools=[
            Tool(id="search", name="search", module="tools"),
            Tool(id="exec", name="exec_command", module="dangerous")
        ]
    )
    policy = Policy(
        metadata=PolicyMetadata(name="Limited"),
        boundaries={
            "tool": {
                "allowed_tools": ["search"],
                "denied_tools": []
            }
        }
    )

    result = ConformanceResult(sbom, policy)
    result.detect_violations()
    score = result.calculate_score()

    assert score < 100
    assert len(result.violations) == 1
    assert "exec_command" in result.violations[0].description


def test_conformance_score_calculation():
    """Test compliance score calculation"""
    result = ConformanceResult(None, None)
    result.violations = [
        Violation("test", "violation 1", "critical"),
        Violation("test", "violation 2", "high"),
    ]

    score = result.calculate_score()
    assert score == 85  # 100 - (10 + 5)
    assert result.verdict == "WARN"


def test_empty_allowed_tools_denies_everything():
    """allowed_tools: [] means deny-by-default, not fail-open"""
    sbom = SBOM(
        agent_path="/agent.py",
        metadata=Metadata(framework="langgraph"),
        tools=[
            Tool(id="search", name="search", module="tools"),
            Tool(id="fetch", name="fetch_url", module="tools"),
        ]
    )
    policy = Policy(
        metadata=PolicyMetadata(name="Empty"),
        boundaries={
            "tool": {
                "allowed_tools": [],
                "denied_tools": []
            }
        }
    )

    result = ConformanceResult(sbom, policy)
    result.detect_violations()
    score = result.calculate_score()

    assert len(result.violations) == 2
    assert all(v.type == "tool_not_allowed" for v in result.violations)
    assert score == 90
    assert result.verdict == "WARN"


def test_missing_allowed_tools_key_skips_allow_check():
    """No allow-list declared at all => no allow-list constraint"""
    sbom = SBOM(
        agent_path="/agent.py",
        metadata=Metadata(framework="langgraph"),
        tools=[Tool(id="search", name="search", module="tools")]
    )
    policy = Policy(
        metadata=PolicyMetadata(name="NoAllowList"),
        boundaries={
            "tool": {
                "denied_tools": []
            }
        }
    )

    result = ConformanceResult(sbom, policy)
    result.detect_violations()
    score = result.calculate_score()

    assert score == 100
    assert len(result.violations) == 0


def test_denied_tools_enforced():
    """A tool present in denied_tools is a critical violation even if allowed"""
    sbom = SBOM(
        agent_path="/agent.py",
        metadata=Metadata(framework="langgraph"),
        tools=[Tool(id="delete_repo", name="delete_repo", module="tools")]
    )
    policy = Policy(
        metadata=PolicyMetadata(name="DenySome"),
        boundaries={
            "tool": {
                "allowed_tools": ["delete_repo"],
                "denied_tools": ["delete_repo"]
            }
        }
    )

    result = ConformanceResult(sbom, policy)
    result.detect_violations()
    result.calculate_score()

    deny_violations = [v for v in result.violations if v.type == "tool_denied"]
    assert len(deny_violations) == 1
    assert deny_violations[0].severity == "critical"
    assert "delete_repo" in deny_violations[0].description


def _cap_tool(name, caps, params=None):
    return Tool(id=name, name=name, module="tools",
                parameters=params or [], capabilities=caps)


def _cap_sbom(tools):
    return SBOM(agent_path="/a.py", metadata=Metadata(framework="langgraph"),
                tools=tools)


def _policy(boundaries):
    return Policy(metadata=PolicyMetadata(name="p"), boundaries=boundaries)


def test_filesystem_read_only_flags_file_write():
    from apcv.core.utils.sbom import ToolParameter
    sbom = _cap_sbom([
        _cap_tool("write_report", ["file_write"],
                  [ToolParameter(name="file_path", type="str")]),
        _cap_tool("search", ["network"],
                  [ToolParameter(name="query", type="str")]),
    ])
    policy = _policy({"filesystem": {"read_only": True, "allowed_paths": [], "denied_paths": []}})

    result = ConformanceResult(sbom, policy)
    result.detect_violations()

    fs = [v for v in result.violations if v.type == "filesystem_read_only"]
    assert len(fs) == 1
    assert "write_report" in fs[0].description


def test_filesystem_not_read_only_no_violation():
    sbom = _cap_sbom([_cap_tool("write_report", ["file_write"])])
    policy = _policy({"filesystem": {"read_only": False}})

    result = ConformanceResult(sbom, policy)
    result.detect_violations()
    assert result.violations == []


def test_network_disabled_flags_user_controllable_egress():
    from apcv.core.utils.sbom import ToolParameter
    sbom = _cap_sbom([
        _cap_tool("fetch_external_url", ["network"],
                  [ToolParameter(name="url", type="str")]),
    ])
    policy = _policy({"network": {"network_enabled": False}})

    result = ConformanceResult(sbom, policy)
    result.detect_violations()

    net = [v for v in result.violations if v.type == "network_egress"]
    assert len(net) == 1
    assert "fetch_external_url" in net[0].description


def test_network_disabled_ignores_fixed_internal_calls():
    """A network tool with no URL parameter (fixed internal endpoint) is not egress."""
    from apcv.core.utils.sbom import ToolParameter
    sbom = _cap_sbom([
        _cap_tool("search_help_articles", ["network"],
                  [ToolParameter(name="query", type="str")]),
    ])
    policy = _policy({"network": {"network_enabled": False}})

    result = ConformanceResult(sbom, policy)
    result.detect_violations()
    assert result.violations == []


def test_network_enabled_no_violation():
    from apcv.core.utils.sbom import ToolParameter
    sbom = _cap_sbom([
        _cap_tool("fetch_external_url", ["network"],
                  [ToolParameter(name="url", type="str")]),
    ])
    policy = _policy({"network": {"network_enabled": True}})

    result = ConformanceResult(sbom, policy)
    result.detect_violations()
    assert result.violations == []
