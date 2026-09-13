"""Unit tests for IsolatedExecutor that do NOT require Docker.

These verify the executor's pure behavior: availability detection short-circuits
when the binary is missing, and the docker-run arg assembly. The actual
container execution lives in tests/integration/test_isolated_execution.py
(gated behind `@pytest.mark.docker`).
"""
import pytest

from apcv.core.execution.executor import IsolatedExecutor, DockerUnavailableError
from apcv.core.execution.sandbox import build_docker_run_args
from apcv.core.policy.schema import Policy, Metadata
from apcv.core.probes.probe import Probe


def _policy(**boundaries):
    return Policy(metadata=Metadata(name="test"), boundaries=boundaries)


def _probe(**kwargs):
    base = dict(
        id="fs_read_1",
        category="filesystem",
        description="d",
        test_command="cat /etc/passwd",
        expected_outcome="denied",
        execution="shell",
    )
    base.update(kwargs)
    return Probe(**base)


def test_docker_available_false_when_binary_missing():
    executor = IsolatedExecutor(docker_bin="definitely-not-a-real-docker-binary")
    assert executor.docker_available() is False


def test_execute_probe_raises_when_docker_missing():
    executor = IsolatedExecutor(docker_bin="definitely-not-a-real-docker-binary")
    with pytest.raises(DockerUnavailableError):
        executor.execute_probe(_probe(), _policy())


def test_run_args_assembly_via_executor():
    """The executor composes image + shell command correctly."""
    args = build_docker_run_args(
        _policy(filesystem={"read_only": True}),
        "img",
        ["/bin/sh", "-c", "cat /etc/passwd"],
    )
    assert args[-4] == "img"
    assert args[-3:] == ["/bin/sh", "-c", "cat /etc/passwd"]
