"""Container entry point for agent probes.

Runs INSIDE the apcv-probe container. It loads the agent file (mounted at
/agent), registers its @tool functions in a ProbeHost, executes the given agent
probes against it, and prints the resulting traces as JSON on stdout. The host
executor parses that JSON — no agent tool code or probe payload ever runs on
the host.

Usage (inside container):
    python entrypoint.py --agent /agent/agent.py --probe "agent.call_tool(...)"
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True, help="path to agent file inside container")
    parser.add_argument("--probe", required=True, help="agent probe test_command to exec")
    args = parser.parse_args()

    host = _load_host(args.agent)

    try:
        exec(args.probe, {"agent": host})
        violation = True
        output = ""
    except Exception as e:
        violation = False
        output = f"{type(e).__name__}: {e}"

    result = {
        "violation": violation,
        "output": output,
        "traces": [t.model_dump() for t in host.drain_traces()],
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
