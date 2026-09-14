"""Container entry point for agent probes.

Runs INSIDE the apcv-probe container. It loads the agent file (mounted at
/agent), registers its @tool functions in a ProbeHost, executes the given agent
probes against it, and prints the resulting traces as JSON on stdout. The host
executor parses that JSON — no agent tool code or probe payload ever runs on
the host.

Usage (inside container):
    python entrypoint.py --agent /agent/agent.py --probe "agent.call_tool(...)"
    python entrypoint.py --agent /agent/agent.py --probe "..." --canary code_exec
"""
from __future__ import annotations

import argparse
import json
import sys


def _load_host(agent_path: str):
    # Import apcv execution machinery inside the container. The probe image
    # ships apcv into site-packages (see Dockerfile).
    from apcv.core.execution.probe_host import ProbeHost

    host = ProbeHost()
    host.load_agent_file(agent_path)
    return host


def _run_shallow(host, probe: str) -> dict:
    """Shallow tier: violation = the tool accepted the payload (no exception)."""
    try:
        exec(probe, {"agent": host})
        return {"violation": True, "output": ""}
    except Exception as e:  # noqa: BLE001
        return {"violation": False, "output": f"{type(e).__name__}: {e}"}


def _run_canary(host, probe: str, canary_type: str) -> dict:
    """Deep tier: violation = the sentinel was actually triggered.

    Sets up the sentinel, runs the probe, then checks whether the sentinel was
    touched. Unlike the shallow tier, a successful call is not enough — the
    dangerous sink must have really fired.
    """
    from apcv.core.execution.canary import setup_canary, check_canary

    setup_canary(canary_type)
    try:
        exec(probe, {"agent": host})
        tool_error = ""
    except Exception as e:  # noqa: BLE001
        tool_error = f"{type(e).__name__}: {e}"

    traces = host.drain_traces()
    triggered = check_canary(canary_type, {}, [t.result for t in traces])
    return {
        "violation": triggered,
        "output": "" if triggered else (tool_error or "sentinel not triggered"),
        "canary_triggered": triggered,
        "traces": [t.model_dump() for t in traces],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True, help="path to agent file inside container")
    parser.add_argument("--probe", required=True, help="agent probe test_command to exec")
    parser.add_argument("--canary", required=False, default="", help="canary type for deep probes")
    args = parser.parse_args()

    host = _load_host(args.agent)

    if args.canary:
        result = _run_canary(host, args.probe, args.canary)
    else:
        result = _run_shallow(host, args.probe)
        result["traces"] = [t.model_dump() for t in host.drain_traces()]

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
