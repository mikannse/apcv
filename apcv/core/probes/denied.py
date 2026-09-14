"""Denied-tool probes (SBOM-driven).

For each tool the policy explicitly denies, emit a probe that really calls it
with placeholder arguments. If the call succeeds (no exception), the denied
capability is reachable at runtime — stronger evidence than the static name
match alone. This replaces the old hard-coded `dangerous_tool` probe, which
never matched a real agent and always bounced off ProbeHost's registry.
"""
from typing import List

from apcv.core.probes.baseline import _arg_literal
from apcv.core.probes.probe import Probe
from apcv.core.policy.schema import Policy
from apcv.core.utils.sbom import SBOM


def generate_denied_tool_probes(sbom: SBOM, policy: Policy) -> List[Probe]:
    """Generate one runtime-reachability probe per policy-denied tool.

    Only tools that BOTH appear in the SBOM and are named in the policy's
    `denied_tools` get a probe. A tool in `denied_tools` but absent from the
    agent's tool surface produces no probe (there is nothing to invoke).
    """
    boundaries = policy.boundaries or {}
    tool_boundary = boundaries.get("tool")
    if not isinstance(tool_boundary, dict):
        return []
    denied = tool_boundary.get("denied_tools", []) or []
    if not denied:
        return []

    probes: List[Probe] = []
    for tool in sbom.tools:
        if tool.name not in denied:
            continue

        args_literal = ", ".join(
            f"'{p.name}': {_arg_literal(p.name, p.type, p.default)}"
            for p in tool.parameters
        )
        probes.append(
            Probe(
                id=f"denied_{tool.name}",
                category="tool",
                description=(
                    f"Invoke denied tool '{tool.name}' to confirm it is "
                    "reachable at runtime"
                ),
                test_command=f"agent.call_tool('{tool.name}', {{{args_literal}}})",
                expected_outcome="Denied tool is not reachable at runtime",
                execution="agent",
                severity="critical",
            )
        )
    return probes
