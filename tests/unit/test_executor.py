"""Unit tests for IsolatedExecutor that do NOT require Docker.

These verify the executor's pure behavior: availability detection short-circuits
when the binary is missing. The actual container execution lives in
tests/integration/test_isolated_execution.py (gated behind `@pytest.mark.docker`).
"""
import pytest

from apcv.core.execution.executor import IsolatedExecutor, DockerUnavailableError
from apcv.core.policy.schema import Policy, Metadata
from apcv.core.probes.probe import Probe


def _policy(**boundaries):
    return Policy(metadata=Metadata(name="test"), boundaries=boundaries)


def _agent_probe():
    return Probe(
        id="tool_undeclared_1",
        category="tool",
        description="d",
        test_command="agent.call_tool('x', {})",
        expected_outcome="denied",
        execution="agent",
    )


def test_docker_available_false_when_binary_missing():
    executor = IsolatedExecutor(docker_bin="definitely-not-a-real-docker-binary")
    assert executor.docker_available() is False


def test_execute_agent_probes_raises_when_docker_missing():
    executor = IsolatedExecutor(docker_bin="definitely-not-a-real-docker-binary")
    with pytest.raises(DockerUnavailableError):
        executor.execute_agent_probes([_agent_probe()], "agent.py", _policy())
