"""wrapt-based parameter tracer.

Records every tool invocation as a TraceRecord (audit-grade evidence for CAP-6).
Supports both sync and async callables via wrapt's adapter. The recorded
arguments and results are stringified; the raw parameter values are what a
compliance auditor needs to prove "this tool was invoked with these arguments
at this time".
"""
from __future__ import annotations

import inspect
from datetime import datetime
from typing import Any, Dict, List

import wrapt

from apcv.core.execution.trace_model import TraceRecord

# Process-global trace buffer. The ProbeHost collects into this; the container
# runner drains it and serializes to JSONL at the end of a probe run.
_TRACES: List[TraceRecord] = []


def _now() -> str:
    return datetime.utcnow().isoformat()


def _stringify(value: Any) -> str:
    try:
        return str(value)
    except Exception:
        return f"<unrepresentable:{type(value).__name__}>"


def _bind_args(wrapped, args, kwargs) -> Dict[str, Any]:
    """Bind positional+keyword args to parameter names for audit clarity."""
    try:
        sig = inspect.signature(wrapped)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        return dict(bound.arguments)
    except (TypeError, ValueError):
        return {"args": list(args), "kwargs": dict(kwargs)}


def get_traces() -> List[TraceRecord]:
    """Return a snapshot of all recorded traces."""
    return list(_TRACES)


def reset_traces() -> None:
    """Clear the trace buffer (call before each probe run)."""
    _TRACES.clear()


@wrapt.decorator
def traced(wrapped, instance, args, kwargs):
    """Decorator that records a TraceRecord around every call.

    Used as a decorator directly on a function/method. `instance` is None for
    plain functions and set for bound methods.
    """
    tool_name = getattr(wrapped, "__name__", str(wrapped))
    result = None
    status = "ok"
    try:
        result = wrapped(*args, **kwargs)
    except Exception as e:
        status = "error"
        result = f"{type(e).__name__}: {e}"
        raise
    finally:
        _TRACES.append(
            TraceRecord(
                ts=_now(),
                tool=tool_name,
                args=_bind_args(wrapped, args, kwargs),
                result=_stringify(result),
                status=status,
            )
        )
    return result
