"""Integration tests for isolated probe execution (requires Docker).

Skipped when the Docker daemon is unavailable. Marked with `docker` so they can
be excluded with `pytest -m "not docker"`.
"""
import pytest

from apcv.core.execution.executor import IsolatedExecutor, DockerUnavailableError
from apcv.core.policy.schema import Policy, Metadata
from apcv.core.probes.probe import Probe


pytestmark = pytest.mark.docker


def _policy(**boundaries):
    return Policy(metadata=Metadata(name="test"), boundaries=boundaries)


def _probe(**kwargs):
    base = dict(
        id="probe_x",
        category="filesystem",
        description="d",
        test_command="true",
        expected_outcome="denied",
        execution="shell",
    )
    base.update(kwargs)
    return Probe(**base)


@pytest.fixture(scope="module")
def executor():
    ex = IsolatedExecutor()
    if not ex.docker_available():
        pytest.skip("Docker daemon not available")
    ex.build_image_if_missing()
    return ex


def test_execute_benign_command_succeeds(executor):
    """A `true` command exits 0; since this probe is framed as a boundary
    attempt, success is recorded as a violation (sandbox did not block it).
    """
    trace = executor.execute_probe(
        _probe(test_command="true"),
        _policy(),
    )
    assert trace.exit_code == 0
    assert trace.violation is True


def test_execute_failing_command_is_not_violation(executor):
    """A failing command (exit != 0) is recorded as blocked, not a violation."""
    trace = executor.execute_probe(
        _probe(test_command="cat /nonexistent-file-xyz"),
        _policy(),
    )
    assert trace.exit_code != 0
    assert trace.violation is False


def test_parallel_execution_returns_all_traces(executor):
    probes = [
        _probe(id="p1", test_command="true"),
        _probe(id="p2", test_command="false"),
    ]
    traces = executor.execute_parallel(probes, _policy())
    assert len(traces) == 2
    assert {t.probe_id for t in traces} == {"p1", "p2"}
