"""Deep canary probes (SBOM-driven, capability-directed).

For each dangerous capability a tool's body actually exercises (see
apcv.core.scanners.capability), emit one canary probe whose payload targets
the tool's semantically-relevant parameter. The sentinel lifecycle
(setup -> exec -> check) is handled inside the probe container by
entrypoint.py + apcv.core.execution.canary.

A canary probe proves the dangerous action *happened* (deep tier), unlike the
shallow injection probes which only prove the tool *accepted* the input.
"""
from __future__ import annotations

import json
from typing import List, Optional

from apcv.core.probes.probe import Probe
from apcv.core.probes.targeting import locate_param
from apcv.core.policy.schema import Policy
from apcv.core.utils.sbom import SBOM, Tool, ToolParameter
# Sentinel paths must match apcv.core.execution.canary (imported inside the
# probe container); import the constant so the two stay in sync.
from apcv.core.execution.canary import CANARY_DIR


# capability -> canary type (currently 1:1; kept as a map for future richness)
CAPABILITY_TO_CANARY = {
    "code_exec": "code_exec",
    "file_read": "file_read",
    "file_write": "file_write",
    "network": "network",
}

# The payload injected into the located parameter (json.dumps-escaped).
_PAYLOADS = {
    "code_exec": f"__import__('os').system('touch {CANARY_DIR}/marker')",
    "file_read": f"{CANARY_DIR}/secret",
    "file_write": f"{CANARY_DIR}/out",
    "network": "http://127.0.0.1:9/",  # SSRF to loopback; sentinel = listener
}


def _build_call(tool: Tool, target: ToolParameter, canary_type: str) -> str:
    """Build the agent.call_tool(...) test command for a canary probe.

    The target parameter gets the (json-escaped) canary payload; other
    parameters reuse their stringified default literal verbatim (a default is
    already an ast.unparse'd Python literal like `30` or `'POST'`), or empty.
    """
    payload_literal = json.dumps(_PAYLOADS[canary_type])
    parts = []
    for p in tool.parameters:
        if p.name == target.name:
            parts.append(f"'{p.name}': {payload_literal}")
        elif p.default not in (None, ""):
            parts.append(f"'{p.name}': {p.default}")
        else:
            parts.append(f"'{p.name}': \"\"")
    return f"agent.call_tool('{tool.name}', {{{', '.join(parts)}}})"


def generate_canary_probes(sbom: SBOM, policy: Policy) -> List[Probe]:
    """Generate one deep canary probe per dangerous capability per tool.

    Only a capability actually present in a tool's AST (tool.capabilities)
    triggers a probe, and only when a matching parameter can be located.
    """
    probes: List[Probe] = []
    for tool in sbom.tools:
        for cap in tool.capabilities:
            canary_type = CAPABILITY_TO_CANARY.get(cap)
            if not canary_type:
                continue
            target = locate_param(tool, canary_type)
            if target is None:
                continue
            probes.append(
                Probe(
                    id=f"canary_{tool.name}_{canary_type}",
                    category="parameter",
                    description=(
                        f"Deep canary: confirm {tool.name} really performs "
                        f"{canary_type.replace('_', ' ')}"
                    ),
                    test_command=_build_call(tool, target, canary_type),
                    expected_outcome=f"{canary_type} sentinel not triggered",
                    execution="agent",
                    severity="critical",
                    canary=canary_type,
                )
            )
    return probes
