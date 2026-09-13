"""Translate a Policy into sandbox (Docker) run parameters.

This is a pure function — no Docker calls — so the mapping logic is covered by
plain unit tests without requiring a running Docker daemon. The executor
(executor.py) consumes the result of these helpers.

Per the change proposal, the "environment probes" (shell category) exist only to
self-check the sandbox build (i.e. they assert this translation is correct);
the security signal lives in the "agent" probes executed against ProbeHost.
"""
from typing import Dict, List, Any, Optional
from apcv.core.policy.schema import Policy


# Non-root UID used by default so shell probes can't trivially escalate.
DEFAULT_USER = "1000:1000"


def build_sandbox_config(policy: Policy) -> Dict[str, Any]:
    """Derive sandbox constraints from a policy.

    Returns a dict describing the isolation posture the policy demands:
      - read_only:   root filesystem mounted read-only
      - network:     whether the container gets network access
      - user:        non-root UID to run as
    """
    boundaries = policy.boundaries or {}

    fs = boundaries.get("filesystem", {}) or {}
    net = boundaries.get("network", {}) or {}

    read_only = bool(fs.get("read_only", False))
    network_enabled = bool(net.get("network_enabled", False))

    return {
        "read_only": read_only,
        "network_enabled": network_enabled,
        "user": DEFAULT_USER,
    }


def build_docker_run_args(
    policy: Policy,
    image: str,
    command: List[str],
    entrypoint: Optional[str] = None,
) -> List[str]:
    """Build the `docker run` argument list for a probe.

    Args:
        policy: the declared policy (drives isolation flags)
        image: probe container image name
        command: the command to run inside the container (argv list)
        entrypoint: if given, override the image ENTRYPOINT (e.g. "/bin/sh"
            for shell probes, since the image's default ENTRYPOINT is the
            agent-probe runner).

    Returns:
        A list of args suitable for `docker run` (before the image name).
    """
    config = build_sandbox_config(policy)

    args: List[str] = ["run", "--rm"]

    if config["network_enabled"]:
        args.append("--network=bridge")
    else:
        args.append("--network=none")

    if config["read_only"]:
        args.append("--read-only")
        # A read-only root FS needs a writable tmpfs so commands can still
        # open temp files (e.g. shell init). Isolation is preserved because
        # tmpfs is ephemeral and not shared.
        args.append("--tmpfs=/tmp:rw,noexec,nosuid,size=16m")

    # Run as non-root so fs/privilege probes can't trivially succeed.
    args.append(f"--user={config['user']}")

    if entrypoint is not None:
        args.append("--entrypoint")
        args.append(entrypoint)

    args.append(image)
    args.extend(command)
    return args
