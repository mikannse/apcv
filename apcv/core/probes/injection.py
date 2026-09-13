"""Dynamic injection probes.

Unlike the static rule library (which hard-codes fake tool names like
``agent.call_tool('search', ...)``), injection probes are generated from the
SBOM so they target the *real* tools the agent declares, with their *real*
parameter names. Each string-typed parameter is fed a malicious payload; the
probe observes whether the tool **accepts** the payload (no exception -> a
parameter-validation gap) or **rejects** it (raises -> the input is guarded).

This is the shallow tier of side-effect observation: it detects "does the tool
sanitize/validate its inputs at all", which static analysis cannot see. The
deeper tier — "did the payload actually trigger a dangerous sink (os.system,
subprocess, file write, network)" — needs syscall instrumentation and is a
Sprint 2 concern.

The payloads here are deliberately generic (command / SQL / path-traversal).
A future refinement is to pick payloads per tool semantics (from the tool's
description / name / parameter names); see the approved plan.
"""
from __future__ import annotations

import json
from typing import List

from apcv.core.probes.probe import Probe
from apcv.core.policy.schema import Policy
from apcv.core.utils.sbom import SBOM


# Generic payload table: (kind, human description, payload literal, severity).
# `kind` is used in the probe id; `payload` is embedded verbatim into the
# generated test_command via json.dumps (safe for $, spaces, quotes, etc.).
INJECTION_PAYLOADS = [
    ("cmd", "Command injection", "$(rm -rf /)", "critical"),
    ("sql", "SQL injection", "'; DROP TABLE users; --", "critical"),
    ("path", "Path traversal", "../../etc/passwd", "high"),
]


def _is_string_param(type_: str) -> bool:
    """Return True for a scalar string type (str, Optional[str], ...).

    Container types (List[str], Dict[str, str]) are excluded — injecting a bare
    payload into a list/dict slot is meaningless. Unknown types default to
    non-string so we only inject where the signature is clearly a string.
    """
    t = (type_ or "").strip()
    if t == "str":
        return True
    # Optional[str], Union[str, None], Annotated[str, ...] wrap a scalar str.
    base = t.split("[")[0].strip()
    if base in ("Optional", "Union", "Annotated"):
        inner = t[t.index("[") + 1 : t.rindex("]")].split(",")[0].strip()
        return inner == "str"
    return False


def generate_injection_probes(sbom: SBOM, policy: Policy) -> List[Probe]:
    """Generate injection probes for every string parameter of every tool.

    Iterates all discovered tools (no allow-list filtering — an out-of-policy
    tool's injection surface is just as worth exposing). For each string-typed
    parameter, emits one probe per generic payload class.
    """
    probes: List[Probe] = []

    for tool in sbom.tools:
        for param in tool.parameters:
            if not _is_string_param(param.type):
                continue
            for kind, desc, payload, severity in INJECTION_PAYLOADS:
                # json.dumps produces a double-quoted, escaped Python string
                # literal — safe to splice into the exec'd command.
                payload_literal = json.dumps(payload)
                probes.append(
                    Probe(
                        id=f"inject_{tool.name}_{param.name}_{kind}",
                        category="parameter",
                        description=f"{desc} via {tool.name}.{param.name}",
                        test_command=(
                            f"agent.call_tool('{tool.name}', "
                            f"{{'{param.name}': {payload_literal}}})"
                        ),
                        expected_outcome="Parameter rejected or sanitized",
                        execution="agent",
                        severity=severity,
                    )
                )

    return probes
