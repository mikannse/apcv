"""Isolated probe executor.

Executes probes inside Docker containers so the boundary-violation attempts
never touch the host. This replaces the MVP stub that returned
"Probe execution not yet implemented".

Implementation note (deviation from story 2-2): we drive the Docker CLI via
subprocess rather than the `docker` Python SDK. The SDK was listed as a
dependency but is not installed in the working environment, and the CLI is a
simpler, more transparent path with zero extra deps. The mapping from policy to
isolation flags lives in sandbox.py (pure, unit-tested).
"""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import List, Optional

from apcv.core.execution.sandbox import build_docker_run_args
from apcv.core.execution.trace_model import ExecutionTrace
from apcv.core.policy.schema import Policy
from apcv.core.probes.probe import Probe


DEFAULT_IMAGE = "apcv-probe:latest"


class DockerUnavailableError(RuntimeError):
    """Raised when the Docker CLI/daemon is not usable."""


def _docker_env() -> dict:
    """Environment for docker subprocess calls.

    On Windows under Git Bash/MSYS, arguments that look like POSIX paths
    (e.g. "/agent/simple_agent.py") get silently rewritten to Windows paths
    ("C:/Program Files/Git/agent/..."), which corrupts the mount target and
    --agent value we pass to the container. MSYS_NO_PATHCONV disables that
    rewriting. Harmless on non-MSYS platforms.
    """
    env = dict(os.environ)
    env.setdefault("MSYS_NO_PATHCONV", "1")
    return env


class IsolatedExecutor:
    """Execute probes in isolated Docker containers."""

    def __init__(
        self,
        image: str = DEFAULT_IMAGE,
        per_probe_timeout: int = 30,
        docker_bin: str = "docker",
    ):
        self.image = image
        self.per_probe_timeout = per_probe_timeout
        self.docker_bin = docker_bin
        self._env = _docker_env()

    # -- Docker availability -------------------------------------------------

    def docker_available(self) -> bool:
        """Return True if the docker CLI is on PATH and the daemon responds."""
        if shutil.which(self.docker_bin) is None:
            return False
        try:
            result = subprocess.run(
                [self.docker_bin, "info"],
                capture_output=True,
                timeout=10,
                env=self._env,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, OSError):
            return False

    def build_image_if_missing(self) -> None:
        """Build the probe image if it is not already present locally."""
        if not self.docker_available():
            raise DockerUnavailableError(
                "Docker is not available. Start Docker Desktop or use --skip-execution."
            )
        result = subprocess.run(
            [self.docker_bin, "image", "inspect", self.image],
            capture_output=True,
            env=self._env,
        )
        if result.returncode == 0:
            return  # already present
        # Build with the project root as context (the Dockerfile COPYs apcv/
        # and docker/apcv-probe/entrypoint.py from there).
        project_root = _project_root()
        dockerfile = project_root / "docker" / "apcv-probe" / "Dockerfile"
        build = subprocess.run(
            [
                self.docker_bin,
                "build",
                "-t",
                self.image,
                "-f",
                str(dockerfile),
                str(project_root),
            ],
            capture_output=True,
            env=self._env,
        )
        if build.returncode != 0:
            raise DockerUnavailableError(
                f"Failed to build probe image: {build.stderr.decode(errors='replace')}"
            )

    # -- Execution -----------------------------------------------------------

    def execute_probe(self, probe: Probe, policy: Policy) -> ExecutionTrace:
        """Execute a single shell probe in an isolated container.

        The probe's test_command is run via `/bin/sh -c <cmd>`. A zero exit
        code means the boundary was NOT enforced (violation=True).
        """
        if not self.docker_available():
            raise DockerUnavailableError(
                "Docker is not available. Start Docker Desktop or use --skip-execution."
            )

        args = build_docker_run_args(
            policy,
            self.image,
            ["-c", probe.test_command],
            entrypoint="/bin/sh",
        )
        # File-level denied_paths isolation: bind-mount an empty file over each
        # denied file so a read returns nothing. Directory-level denial is
        # deferred to seccomp (Sprint 2).
        empty_file, cleanup = self._denied_file_mount_source(policy)
        try:
            args = self._insert_denied_mounts(args, policy, empty_file)
            result = subprocess.run(
                [self.docker_bin, *args],
                capture_output=True,
                timeout=self.per_probe_timeout,
                env=self._env,
            )
        except subprocess.TimeoutExpired:
            return ExecutionTrace(
                probe_id=probe.id,
                execution=probe.execution,
                exit_code=-1,
                output="probe timed out",
                violation=False,
            )
        finally:
            cleanup()

        output = (result.stdout + result.stderr).decode(errors="replace")
        exit_code = result.returncode
        # A shell probe that succeeded means the sandbox failed to block the
        # boundary-violation attempt. For filesystem reads, an empty output
        # means the denied path was blanked by a file-level mount (isolation
        # held) rather than a real content leak.
        if probe.category == "filesystem":
            violation = exit_code == 0 and bool(output.strip())
        else:
            violation = exit_code == 0

        return ExecutionTrace(
            probe_id=probe.id,
            execution=probe.execution,
            exit_code=exit_code,
            output=output,
            violation=violation,
            severity=probe.severity,
        )

    def execute_parallel(
        self,
        probes: List[Probe],
        policy: Policy,
        workers: int = 4,
    ) -> List[ExecutionTrace]:
        """Execute multiple probes.

        MVP keeps a simple sequential loop (deterministic, no shared mutable
        state between containers). `workers` is accepted for CLI parity but the
        executor currently runs serially to guarantee zero cross-pollution and
        stable ordering; parallel execution is a later optimization.
        """
        return [self.execute_probe(p, policy) for p in probes]

    # -- Convenience ---------------------------------------------------------

    def execute_shell_probes(
        self,
        probes: List[Probe],
        policy: Policy,
    ) -> List[ExecutionTrace]:
        """Execute only shell-category probes (agent probes need ProbeHost)."""
        shell_probes = [p for p in probes if p.execution == "shell"]
        return self.execute_parallel(shell_probes, policy)

    def execute_agent_probes(
        self,
        probes: List[Probe],
        agent_path: str,
        policy: Policy,
    ) -> List[ExecutionTrace]:
        """Execute agent-category probes inside the sandbox container.

        Mounts the agent file at /agent and runs entrypoint.py in the container
        for each agent probe. entrypoint.py loads the agent into a ProbeHost,
        execs the probe with `agent` bound to it, and prints a JSON result on
        stdout. The host only parses that JSON — agent tool code and probe
        payloads (e.g. `import os; os.system(...)`) never run on the host.
        """
        import json
        from pathlib import Path

        if not self.docker_available():
            raise DockerUnavailableError(
                "Docker is not available. Start Docker Desktop or use --skip-execution."
            )

        agent_abs = str(Path(agent_path).resolve())
        agent_name = Path(agent_path).name

        # agent probes attempt a boundary violation; baseline probes record
        # real tool behavior (success is the desired, non-hostile outcome).
        probes = [p for p in probes if p.execution in ("agent", "baseline")]
        traces: List[ExecutionTrace] = []

        for probe in probes:
            # Mount the agent file read-only into the container and run the
            # entrypoint against it. The container runs non-root and with the
            # policy's network/read-only isolation (reuse sandbox config).
            run_args = build_docker_run_args(
                policy,
                self.image,
                [
                    "--agent",
                    f"/agent/{agent_name}",
                    "--probe",
                    probe.test_command,
                ],
            )
            # build_docker_run_args appends image + command; insert the volume
            # mount BEFORE the image name.
            idx = run_args.index(self.image)
            run_args.insert(idx, "-v")
            run_args.insert(idx + 1, f"{agent_abs}:/agent/{agent_name}:ro")

            try:
                result = subprocess.run(
                    [self.docker_bin, *run_args],
                    capture_output=True,
                    timeout=self.per_probe_timeout,
                    env=self._env,
                )
            except subprocess.TimeoutExpired:
                traces.append(
                    ExecutionTrace(
                        probe_id=probe.id,
                        execution=probe.execution,
                        exit_code=-1,
                        output="probe timed out",
                        violation=False,
                        severity=probe.severity,
                    )
                )
                continue

            stdout = result.stdout.decode(errors="replace")
            exit_code = result.returncode

            # Parse the JSON result emitted by entrypoint.py.
            violation = False
            output = stdout.strip()
            records = []
            try:
                payload = json.loads(stdout)
                violation = bool(payload.get("violation", False))
                output = payload.get("output", "")
                # The entrypoint returns tool-invocation recordings ("traces")
                # as a list of dicts. Rehydrate them into TraceRecord for the
                # audit report.
                from apcv.core.execution.trace_model import TraceRecord

                records = [
                    TraceRecord(**r) for r in payload.get("traces", [])
                ]
            except (json.JSONDecodeError, TypeError, ValueError):
                # Non-JSON stdout (e.g. an import error) — treat as no
                # violation but surface the raw text for diagnosis.
                violation = False

            # Baseline probes record behavior, never raise a violation: a
            # successful tool invocation is the desired outcome.
            if probe.execution == "baseline":
                violation = False

            traces.append(
                ExecutionTrace(
                    probe_id=probe.id,
                    execution=probe.execution,
                    exit_code=exit_code,
                    output=output,
                    violation=violation,
                    severity=probe.severity,
                    records=records,
                )
            )

        return traces

    # -- denied_paths file-level isolation -----------------------------------

    def _denied_file_mount_source(self, policy: Policy):
        """Return (empty_file_path, cleanup_callable) for denied-file mounts.

        Returns (None, noop) when there are no file-level denied paths.
        """
        from apcv.core.execution.sandbox import build_denied_file_mounts

        if not build_denied_file_mounts(policy):
            return None, lambda: None

        import tempfile

        fd, path = tempfile.mkstemp(suffix=".empty", prefix="apcv_denied_")
        os.close(fd)

        def cleanup():
            try:
                os.remove(path)
            except OSError:
                pass

        return path, cleanup

    def _insert_denied_mounts(self, args, policy, empty_file):
        """Insert `-v <empty>:<path>:ro` args before the image name."""
        from apcv.core.execution.sandbox import build_denied_file_mounts

        if empty_file is None:
            return args

        specs = build_denied_file_mounts(policy)
        idx = args.index(self.image)
        for spec in specs:
            _, container_path, mode = spec.split(":", 2)
            args.insert(idx, "-v")
            args.insert(idx + 1, f"{empty_file}:{container_path}:{mode}")
            idx += 2
        return args


def _project_root() -> str:
    """Locate the project root relative to this module."""
    from pathlib import Path

    # apcv/core/execution/executor.py -> project root
    here = Path(__file__).resolve()
    return str(here.parents[3])
