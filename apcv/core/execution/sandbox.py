"""Translate a Policy into sandbox (Docker) run parameters.

This is a pure function — no Docker calls — so the mapping logic is covered by
plain unit tests without requiring a running Docker daemon. The executor
(executor.py) consumes the result of these helpers.

The sandbox is a FIXED isolation cage, not a policy enforcer. Its only job is
to keep agent code and probe payloads off the host. It must NOT apply policy
constraints (denied_paths, read-only, no-network) — doing so would hide the
very boundary-violation behavior APCV exists to detect. The detection signal
comes from agent probes observing real tool behavior, not from a sandbox that
pre-emptively blocks it.
"""
from typing import Dict, List, Any, Optional
from apcv.core.policy.schema import Policy


# Non-root UID used by default so probes can't trivially escalate inside the
# container.
DEFAULT_USER = "1000:1000"


def build_docker_run_args(
    policy: Policy,
    image: str,
    command: List[str],
    entrypoint: Optional[str] = None,
) -> List[str]:
    """Build the `docker run` argument list for a probe.

    The container is always created with a fixed isolation posture:
      - non-root user
      - network disabled (probes must not reach the real internet)
    These are safety isolation, NOT policy enforcement — they are identical for
    every probe regardless of the declared policy.

    Args:
        policy: unused here; kept for signature stability with callers.
        image: probe container image name
        command: the command to run inside the container (argv list)
        entrypoint: if given, override the image ENTRYPOINT (e.g. "/bin/sh"
            for shell probes, since the image's default ENTRYPOINT is the
            agent-probe runner).

    Returns:
        A list of args suitable for `docker run` (before the image name).
    """
    args: List[str] = ["run", "--rm"]

    # Fixed isolation: no network. (Not policy-driven.)
    args.append("--network=none")

    # Run as non-root so probes can't trivially escalate.
    args.append(f"--user={DEFAULT_USER}")

    if entrypoint is not None:
        args.append("--entrypoint")
        args.append(entrypoint)

    args.append(image)
    args.extend(command)
    return args
