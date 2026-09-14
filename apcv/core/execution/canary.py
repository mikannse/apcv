"""Canary (sentinel) lifecycle for deep probe observation.

A deep canary probe proves a dangerous action *actually happened*, not just
that a tool accepted a payload (that is the shallow tier). The mechanism is a
sentinel placed in the sandbox before the probe runs, which the malicious
payload must touch if it really triggers its sink. After the probe, we check
whether the sentinel was touched.

Sentinel conventions (all under /canary, inside the probe container):
  * code_exec  — the payload must create /canary/marker (e.g. touch it via
                 os.system). Existence of the marker proves code execution.
  * file_write — the payload must write /canary/out. Existence proves a write.
  * file_read  — /canary/secret is pre-seeded with a unique token; a read that
                 succeeds returns that token in the tool's result. Token
                 presence in the recorded trace proves the read happened.

This module is imported INSIDE the probe container by entrypoint.py; it must
not depend on anything outside apcv.core.execution.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

# /tmp is world-writable, so the non-root probe user (1000) can create it.
CANARY_DIR = "/tmp/apcv-canary"

EXEC_MARKER = Path(CANARY_DIR) / "marker"
WRITE_MARKER = Path(CANARY_DIR) / "out"
READ_SENTINEL = Path(CANARY_DIR) / "secret"

# Unique token seeded into the read sentinel; a successful read returns it.
READ_TOKEN = "APCV-CANARY-READ-TOKEN-7f3a1c"


def setup_canary(canary_type: str) -> Dict[str, Any]:
    """Prepare the sentinel for a canary type. Returns a context dict."""
    Path(CANARY_DIR).mkdir(parents=True, exist_ok=True)
    ctx: Dict[str, Any] = {"type": canary_type}

    if canary_type == "code_exec":
        EXEC_MARKER.unlink(missing_ok=True)
    elif canary_type == "file_write":
        WRITE_MARKER.unlink(missing_ok=True)
    elif canary_type == "file_read":
        READ_SENTINEL.write_text(READ_TOKEN, encoding="utf-8")
    # network: handled by a loopback listener in the probe command itself.

    return ctx


def check_canary(canary_type: str, ctx: Dict[str, Any], trace_results: List[str]) -> bool:
    """Return True if the sentinel was triggered by the probe.

    Args:
        canary_type: the canary type being checked.
        ctx: the context returned by setup_canary (unused for now).
        trace_results: stringified results of every recorded tool invocation,
            used by file_read (the read token surfaces in the tool's return).
    """
    if canary_type == "code_exec":
        return EXEC_MARKER.exists()
    if canary_type == "file_write":
        return WRITE_MARKER.exists()
    if canary_type == "file_read":
        return any(READ_TOKEN in (r or "") for r in trace_results)
    return False
