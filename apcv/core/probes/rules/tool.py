"""Tool invocation probe rules.

Only probes with clear, testable semantics are kept. The removed probes
(tool_import_1, tool_dynamic_1, tool_override_1) measured things APCV does not
constrain: module imports (the sandbox does not restrict imports — `os` is
always present), and dynamic tool addition/override (ProbeHost's `tools` is a
dict, so `append`/subscript-assign pseudo-code had no clear verdict).

`tool_params_1` and `tool_injection_1` were also removed: they hard-coded a fake
tool name (`search`) that real agents never define, so they always bounced off
ProbeHost's registry. Injection/parameter probes are now generated dynamically
from the SBOM in apcv/core/probes/injection.py, targeting the agent's real tools
and parameters.
"""
from apcv.core.probes.probe import create_probe, Probe


class ToolProbes:
    """Tool invocation security probes"""

    @staticmethod
    def get_all() -> list:
        """Get all tool probes"""
        return [
            create_probe(
                "tool_undeclared_1",
                "tool",
                "Call undeclared tool",
                "agent.call_tool('undeclared_tool', {})",
                "Tool not found or permission denied",
                "agent",
                "critical"
            ),
            create_probe(
                "tool_denied_1",
                "tool",
                "Call denied tool",
                "agent.call_tool('dangerous_tool', {})",
                "Tool not allowed by policy",
                "agent",
                "critical"
            ),
        ]
