"""Tests for output formatters."""
import json
from apcv.cli.output import format_json, format_sarif, format_html


def _report():
    return {
        "verdict": "WARN",
        "compliance_score": 76,
        "tools_discovered": 3,
        "probes_executed": 20,
        "agent_path": "/agent.py",
        "policy_name": "Test Policy",
        "violations": [
            {"type": "tool_not_allowed", "description": "bad tool", "severity": "high"},
        ],
    }


def test_format_json_round_trips():
    d = json.loads(format_json(_report()))
    assert d["verdict"] == "WARN"
    assert d["violations"][0]["type"] == "tool_not_allowed"


def test_format_sarif_structure():
    d = json.loads(format_sarif(_report()))
    assert d["version"] == "2.1.0"
    assert d["runs"][0]["tool"]["driver"]["name"] == "apcv"
    assert len(d["runs"][0]["results"]) == 1
    r = d["runs"][0]["results"][0]
    assert r["ruleId"] == "tool_not_allowed"
    assert r["level"] == "error"  # high -> error


def test_format_sarif_severity_mapping():
    d = json.loads(format_sarif({
        "violations": [
            {"type": "x", "description": "c", "severity": "critical"},
            {"type": "y", "description": "l", "severity": "low"},
        ]
    }))
    levels = [r["level"] for r in d["runs"][0]["results"]]
    assert levels == ["error", "note"]


def test_format_html_escapes_and_renders():
    html = format_html(_report())
    assert "<html" in html
    assert "Test Policy" in html
    assert "tool_not_allowed" in html


def test_format_html_no_violations():
    html = format_html({** _report(), "violations": []})
    assert "No violations" in html
