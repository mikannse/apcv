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
