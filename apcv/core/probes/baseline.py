"""Baseline tool-invocation probes.

Unlike boundary probes (which attempt a violation and flag success), baseline
probes *record the real behavior* of each declared tool. Their only job is to
produce audit evidence (TraceRecord): "on this date, APCV actually invoked tool
X with arguments Y and observed result Z". They never raise a violation — a
successful invocation is the desired, non-hostile outcome.

They are generated dynamically from the SBOM because they need each tool's
parameter signature, which the static rule library does not know.
"""
from typing import List

from apcv.core.probes.probe import Probe
from apcv.core.policy.schema import Policy
from apcv.core.utils.sbom import SBOM


# Type-appropriate placeholders for required parameters that have no default.
_TYPE_PLACEHOLDER = {
    "str": "''",
    "int": "0",
    "float": "0.0",
    "bool": "False",
    "list": "[]",
    "dict": "{}",
}


def _arg_literal(name: str, type_: str, default: str) -> str:
    """Return a Python literal string for one tool argument."""
    if default not in (None, ""):
        # default is already a stringified Python literal from ast.unparse
        # (e.g. "10" or "'x'"), so reuse it verbatim.
        return default
    t = (type_ or "str").lower()
    if t in _TYPE_PLACEHOLDER:
        return _TYPE_PLACEHOLDER[t]
    # Unknown/optional-any: use a neutral string.
    return "''"


def generate_baseline_probes(sbom: SBOM, policy: Policy) -> List[Probe]:
    """Generate one 'record real behavior' probe per declared tool.

    The declared tool surface is derived from the policy's tool boundary:
      - if `allowed_tools` is non-empty, baseline only those tools;
      - otherwise baseline every discovered tool.
    """
    allowed = _declared_tools(policy)

    probes: List[Probe] = []
    for tool in sbom.tools:
        if allowed is not None and tool.name not in allowed:
            continue

        args_literal = ", ".join(
            f"'{p.name}': {_arg_literal(p.name, p.type, p.default)}"
            for p in tool.parameters
        )
        probes.append(
            Probe(
                id=f"baseline_{tool.name}",
                category="tool",
                description=f"Record real behavior of declared tool '{tool.name}'",
                test_command=f"agent.call_tool('{tool.name}', {{{args_literal}}})",
                expected_outcome="Tool invoked; behavior recorded as evidence",
                execution="baseline",
                severity="low",
            )
        )
    return probes


def _declared_tools(policy: Policy):
    """Return the set of declared tools, or None if no allow-list is declared."""
    boundaries = policy.boundaries or {}
    if "tool" not in boundaries:
        return None
    tb = boundaries["tool"]
    if not isinstance(tb, dict):
        return None
    allowed = tb.get("allowed_tools", []) or []
    if not allowed:
        return None
    return set(allowed)
