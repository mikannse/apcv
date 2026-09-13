"""Output formatters for `apcv validate` (json / sarif / html).

The CLI builds a single result dict and hands it to one of these formatters.
SARIF targets CI/CD ingestion (GitHub Code Scanning, GitLab), HTML is a
human-readable report, and JSON is the machine-readable default.
"""
from __future__ import annotations

import json
from typing import Dict, Any, List

SARIF_SCHEMA = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/"
    "Schemata/sarif-schema-2.1.0.json"
)

# Map APCV severity to SARIF level.
_SEVERITY_TO_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
}


def format_json(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False)


def format_sarif(report: Dict[str, Any]) -> str:
    """Render the report as SARIF 2.1.0."""
    violations = report.get("violations", [])

    results: List[Dict[str, Any]] = []
    for v in violations:
        severity = v.get("severity", "high")
        results.append(
            {
                "ruleId": v.get("type", "violation"),
                "level": _SEVERITY_TO_LEVEL.get(severity, "warning"),
                "message": {"text": v.get("description", "")},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": report.get("agent_path", "agent.py")
                            }
                        }
                    }
                ],
            }
        )

    sarif = {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "apcv",
                        "version": report.get("version", "0.1.0"),
                        "informationUri": "https://example.com/apcv",
                    }
                },
                "results": results,
            }
        ],
    }
    return json.dumps(sarif, indent=2, ensure_ascii=False)


def format_html(report: Dict[str, Any]) -> str:
    """Render a minimal human-readable HTML report."""
    violations = report.get("violations", [])
    verdict = report.get("verdict", "UNKNOWN")
    score = report.get("compliance_score", 0)

    color = {"PASS": "#2e7d32", "WARN": "#ed6c02", "FAIL": "#d32f2f"}.get(
        verdict, "#616161"
    )

    rows = "\n".join(
        f"<tr><td>{_esc(v.get('type', ''))}</td>"
        f"<td>{_esc(v.get('severity', ''))}</td>"
        f"<td>{_esc(v.get('description', ''))}</td></tr>"
        for v in violations
    )
    if not rows:
        rows = '<tr><td colspan="3">No violations</td></tr>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>APCV Report — {_esc(report.get('policy_name', ''))}</title>
<style>
body {{ font-family: -apple-system, Segoe UI, sans-serif; margin: 2rem; color: #1a1a1a; }}
.score {{ font-size: 3rem; font-weight: 700; color: {color}; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 1.5rem; }}
th, td {{ text-align: left; padding: .5rem .75rem; border-bottom: 1px solid #ddd; }}
th {{ background: #f5f5f5; }}
</style>
</head>
<body>
<h1>APCV Compliance Report</h1>
<p>Policy: <strong>{_esc(report.get('policy_name', ''))}</strong></p>
<p>Agent: <code>{_esc(report.get('agent_path', ''))}</code></p>
<p class="score">{score}/100 — {_esc(verdict)}</p>
<p>{report.get('tools_discovered', 0)} tools discovered · {report.get('probes_executed', 0)} probes executed</p>
<table>
<thead><tr><th>Type</th><th>Severity</th><th>Description</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>
"""


def _esc(s: str) -> str:
    """Escape HTML special characters."""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
