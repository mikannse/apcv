"""Conformance checker - validates Agent behavior against policy"""
from typing import List, Dict, Any
from apcv.core.utils.sbom import SBOM, Tool
from apcv.core.policy.schema import Policy


class Violation:
    """Policy violation"""
    def __init__(self, violation_type: str, description: str, severity: str = "high"):
        self.type = violation_type
        self.description = description
        self.severity = severity


class ConformanceResult:
    """Result of conformance check"""
    def __init__(self, sbom: SBOM, policy: Policy):
        self.sbom = sbom
        self.policy = policy
        self.violations: List[Violation] = []
        self.compliance_score = 100

    def detect_violations(self):
        """Detect violations between SBOM and policy"""
        if "tool" not in self.policy.boundaries:
            return

        tool_boundary = self.policy.boundaries["tool"]
        denied_tools = tool_boundary.get("denied_tools", []) or []
        # An explicitly declared (even empty) allow-list means deny-by-default.
        # Only a missing key means "no allow-list constraint".
        has_allow_list = "allowed_tools" in tool_boundary
        allowed_tools = tool_boundary.get("allowed_tools", []) or []

        for tool in self.sbom.tools:
            # Deny always wins over allow.
            if tool.name in denied_tools:
                self.violations.append(
                    Violation(
                        "tool_denied",
                        f"Tool '{tool.name}' is explicitly denied by policy",
                        severity="critical",
                    )
                )
                continue

            if has_allow_list and tool.name not in allowed_tools:
                self.violations.append(
                    Violation(
                        "tool_not_allowed",
                        f"Tool '{tool.name}' not in allowed list",
                    )
                )

    def calculate_score(self) -> int:
        """Calculate compliance score (0-100)"""
        if not self.violations:
            return 100

        # Severity weights: critical=10, high=5, medium=2, low=1
        weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        total_weight = sum(weights.get(v.severity, 5) for v in self.violations)

        score = max(0, 100 - total_weight)
        self.compliance_score = score
        return score

    @property
    def verdict(self) -> str:
        """PASS/FAIL/WARN based on compliance"""
        if self.compliance_score >= 95:
            return "PASS"
        elif self.compliance_score >= 70:
            return "WARN"
        else:
            return "FAIL"
