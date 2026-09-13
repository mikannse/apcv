"""Translate a Policy into sandbox (Docker) run parameters.

This is a pure function — no Docker calls — so the mapping logic is covered by
plain unit tests without requiring a running Docker daemon. The executor
(executor.py) consumes the result of these helpers.

Per the change proposal, the "environment probes" (shell category) exist only to
self-check the sandbox build (i.e. they assert this translation is correct);
the security signal lives in the "agent" probes executed against ProbeHost.

denied_paths read-isolation is implemented in two tiers:
  * file-level (e.g. /etc/passwd, /etc/shadow): the executor bind-mounts an
    empty file over the path so reads return nothing. Docker can do this
    cleanly.
  * directory-level (e.g. /etc, /root): Docker cannot shadow a whole directory
    without breaking the container (the image needs /etc to run). This requires
    seccomp/gVisor, which is deferred to Sprint 2 per the architecture.
"""
from typing import Dict, List, Any, Optional, Tuple
from apcv.core.policy.schema import Policy


# Non-root UID used by default so shell probes can't trivially escalate.
DEFAULT_USER = "1000:1000"

# Extension-less paths that are nonetheless files (not directories) and are
# commonly targeted by probes.
_KNOWN_SENSITIVE_FILES = {
    "/etc/passwd",
    "/etc/shadow",
    "/etc/group",
    "/etc/sudoers",
    "/etc/hosts",
    "/etc/hostname",
    "/etc/resolv.conf",
}


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


def _is_file_path(path: str) -> bool:
    """Heuristic: is this denied path a concrete file (mountable) vs a directory?

    Directory-level read isolation needs seccomp; file-level can be done with a
    bind-mount of an empty file. We classify by extension, known sensitive file
    names, or a hidden parent segment (~/.aws/credentials). The heuristic errs
    toward "directory" when uncertain — that is the safe direction, since a
    file mistakenly treated as a directory is merely deferred to seccomp rather
    than mounting an empty file over a live directory.
    """
    cleaned = path.rstrip("/")
    name = cleaned.rsplit("/", 1)[-1]
    if cleaned in _KNOWN_SENSITIVE_FILES:
        return True
    # Has an extension (e.g. .pem, .key, .conf, .json) => likely a file.
    if "." in name and not name.startswith("."):
        return True
    # Hidden parent segment (e.g. /home/u/.aws/credentials, /root/.ssh/id_rsa)
    parent = cleaned.rsplit("/", 1)[0] if "/" in cleaned else ""
    if any(seg.startswith(".") for seg in parent.split("/") if seg):
        return True
    return False


def classify_denied_paths(policy: Policy) -> Tuple[List[str], List[str]]:
    """Split denied_paths into (file_level, directory_level).

    file_level paths can be isolated with an empty-file bind mount now.
    directory_level paths require seccomp/gVisor (deferred to Sprint 2).
    """
    boundaries = policy.boundaries or {}
    fs = boundaries.get("filesystem", {}) or {}
    denied = fs.get("denied_paths", []) or []

    files, dirs = [], []
    for path in denied:
        if _is_file_path(path):
            files.append(path)
        else:
            dirs.append(path)
    return files, dirs


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


def build_denied_file_mounts(policy: Policy) -> List[str]:
    """Return `-v <empty>:<path>:ro` args for file-level denied paths.

    The executor must supply a real empty host file per entry. This helper
    returns just the container-side mount specs (file-level only); directory
    level is deliberately omitted (needs seccomp, deferred).
    """
    files, _ = classify_denied_paths(policy)
    # A single empty host file can be reused for every denied file target.
    # Executor creates it and substitutes the "<EMPTY>" placeholder.
    return [f"<EMPTY>:{path}:ro" for path in files]
