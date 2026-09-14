"""Conformance checker - validates Agent behavior against policy"""
from typing import List, Dict, Any
from apcv.core.utils.sbom import SBOM, Tool
from apcv.core.policy.schema import Policy
from apcv.core.probes.targeting import locate_param


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
        """Detect violations between SBOM and policy across all boundaries."""
        self._detect_tool_violations()
        self._detect_filesystem_violations()
        self._detect_network_violations()

    def _detect_tool_violations(self):
        """Tool boundary: denied tools + allow-list (deny-by-default)."""
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

    def _detect_filesystem_violations(self):
        """Filesystem boundary: read_only forbids file-write capability.

        Precise path matching (denied_paths / allowed_paths) needs data-flow
        analysis and is deferred; capability-level read_only is unambiguous.
        """
        fs = self.policy.boundaries.get("filesystem")
        if not isinstance(fs, dict):
            return
        if not fs.get("read_only", False):
            return

        for tool in self.sbom.tools:
            if "file_write" in tool.capabilities:
                self.violations.append(
                    Violation(
                        "filesystem_read_only",
                        f"Tool '{tool.name}' has file-write capability but "
                        "policy requires a read-only filesystem",
                        severity="high",
                    )
                )

    def _detect_network_violations(self):
        """Network boundary: network_enabled=false forbids arbitrary egress.

        Only flag tools whose network target is user-controllable (a URL-like
        parameter). Whitelisted tools that call a fixed internal endpoint
        (e.g. search_help_articles -> settings.help_center_url) are not
        arbitrary egress. denied_domains/allowed_domains matching needs
        data-flow analysis and is deferred.
        """
        net = self.policy.boundaries.get("network")
        if not isinstance(net, dict):
            return
        if net.get("network_enabled", False):
            return

        for tool in self.sbom.tools:
            if "network" not in tool.capabilities:
                continue
            if locate_param(tool, "network") is None:
                # No user-controllable URL parameter -> fixed internal call.
                continue
            self.violations.append(
                Violation(
                    "network_egress",
                    f"Tool '{tool.name}' has user-controllable network egress "
                    "but policy disables it",
                    severity="high",
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
