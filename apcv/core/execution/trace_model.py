"""Execution trace data models"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ExecutionTrace(BaseModel):
    """Result of executing a single probe.

    Semantics: a probe is a "越界尝试" (boundary-violation attempt). If the
    command succeeds (exit_code == 0), the sandbox did NOT enforce the policy
    constraint, so `violation` is True. A non-zero exit means the sandbox
    correctly blocked the attempt.
    """
    probe_id: str = Field(..., description="Probe ID that produced this trace")
    execution: str = Field(..., description="Execution mode: 'shell' or 'agent'")
    exit_code: int = Field(..., description="Process exit code (0 = success)")
    output: str = Field(default="", description="Captured stdout/stderr")
    violation: bool = Field(default=False, description="True if boundary was breached")
    severity: str = Field(default="high", description="Severity if this is a violation")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


class TraceRecord(BaseModel):
    """A single tool invocation captured by the wrapt parameter tracer (phase 2).

    This is the audit-grade "recording" consumed by CAP-6: for each tool call we
    record when it happened, which tool, what arguments were passed, and the
    result. JSONL-encoded for evidence-chain preservation.
    """
    ts: str = Field(..., description="ISO-8601 timestamp")
    tool: str = Field(..., description="Tool name that was invoked")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed")
    result: str = Field(default="", description="Return value (stringified)")
    status: str = Field(default="ok", description="ok | error")

    def to_jsonl(self) -> str:
        """Serialize as a single JSONL line."""
        import json

        return json.dumps(self.model_dump(), ensure_ascii=False)


class ExecutionReport(BaseModel):
    """Aggregated execution results written to .apcv/reports/ (AD-8)."""
    agent_path: str
    policy_name: str
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    probes_run: int = Field(default=0)
    violations: List[ExecutionTrace] = Field(default_factory=list)
    traces: List[ExecutionTrace] = Field(default_factory=list)
    records: List[TraceRecord] = Field(default_factory=list)
