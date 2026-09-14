"""Shallow injection probes (SBOM-driven, capability-directed).

Each tool with a dangerous capability (see apcv.core.scanners.capability) gets
an injection probe whose payload is *semantically matched* to that capability —
e.g. a code-exec tool receives a real Python snippet, a network tool receives a
SSRF URL, a file tool receives a path traversal. A tool with no detected
capability falls back to the generic command/SQL/path payloads across all its
string parameters.

The probe observes whether the tool **accepts** the payload (no exception -> a
parameter-validation gap) or **rejects** it (raises -> the input is guarded).
This is the shallow tier: it proves "no input validation", not "a dangerous sink
fired" (that is the deep canary tier in apcv.core.probes.canary).

The key improvement over the old generic-only payloads: feeding a code-exec
tool `$(rm -rf /)` is meaningless — it is not valid Python, so the tool raises a
SyntaxError and the shallow tier *misreports* "rejected". A semantically-correct
payload (valid Python that actually runs) is what reveals the validation gap.
"""
from __future__ import annotations

import json
from typing import List

from apcv.core.probes.probe import Probe
from apcv.core.probes.targeting import is_string_param, locate_param
from apcv.core.policy.schema import Policy
from apcv.core.utils.sbom import SBOM


# Generic payloads for tools with no detected capability:
# (kind, human description, payload literal, severity).
GENERIC_INJECTION_PAYLOADS = [
    ("cmd", "Command injection", "$(rm -rf /)", "critical"),
    ("sql", "SQL injection", "'; DROP TABLE users; --", "critical"),
    ("path", "Path traversal", "../../etc/passwd", "high"),
]

# Capability-directed payloads: semantically-valid malicious input per class.
# (capability -> (kind, description, payload, severity)).
CAPABILITY_INJECTION_PAYLOADS = {
    "code_exec": (
        "code_exec",
        "Code injection",
        "__import__('os').system('echo APCV_PWNED')",
        "critical",
    ),
    "network": (
        "ssrf",
        "Server-side request forgery",
        "http://169.254.169.254/latest/meta-data/",
        "critical",
    ),
    "file_read": (
        "path",
        "Path traversal (read)",
        "../../etc/passwd",
        "high",
    ),
    "file_write": (
        "path",
        "Path traversal (write)",
        "../../tmp/apcv-evil",
        "high",
    ),
}


def _make_probe(tool, param_name, kind, desc, payload, severity) -> Probe:
    payload_literal = json.dumps(payload)
    return Probe(
        id=f"inject_{tool.name}_{param_name}_{kind}",
        category="parameter",
        description=f"{desc} via {tool.name}.{param_name}",
        test_command=(
            f"agent.call_tool('{tool.name}', "
            f"{{'{param_name}': {payload_literal}}})"
        ),
        expected_outcome="Parameter rejected or sanitized",
        execution="agent",
        severity=severity,
    )


def _capability_probes(tool) -> List[Probe]:
    """Emit one semantically-matched probe per detected capability."""
    probes: List[Probe] = []
    for cap in tool.capabilities:
        spec = CAPABILITY_INJECTION_PAYLOADS.get(cap)
        if not spec:
            continue
        target = locate_param(tool, cap)
        if target is None:
            continue
        kind, desc, payload, severity = spec
        probes.append(_make_probe(tool, target.name, kind, desc, payload, severity))
    return probes


def _generic_probes(tool) -> List[Probe]:
    """Emit generic cmd/sql/path probes across every string parameter."""
    probes: List[Probe] = []
    for param in tool.parameters:
        if not is_string_param(param):
            continue
        for kind, desc, payload, severity in GENERIC_INJECTION_PAYLOADS:
            probes.append(_make_probe(tool, param.name, kind, desc, payload, severity))
    return probes


def generate_injection_probes(sbom: SBOM, policy: Policy) -> List[Probe]:
    """Generate injection probes for every tool.

    A tool with detected capabilities gets semantically-matched payloads on its
    relevant parameter(s). A tool with no capabilities gets the generic payload
    suite on every string parameter.
    """
    probes: List[Probe] = []
    for tool in sbom.tools:
        if tool.capabilities:
            probes.extend(_capability_probes(tool))
        else:
            probes.extend(_generic_probes(tool))
    return probes
