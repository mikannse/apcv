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

    Uses the privilege category (not filesystem) because filesystem probes
    have a special rule: empty output after a denied-file mount is NOT a
    violation (isolation held, no content leaked).
    """
    trace = executor.execute_probe(
        _probe(test_command="true", category="privilege"),
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


def test_agent_probe_captures_tool_records(executor):
    """A tool-calling agent probe produces audit records on the trace."""
    agent = "tests/fixtures/sample_agents/simple_agent.py"
    probe = _probe(
        id="agent_probe_x",
        category="tool",
        test_command="agent.call_tool('search_documents', {'query': 'test'})",
        execution="agent",
    )
    traces = executor.execute_agent_probes([probe], agent, _policy())

    assert len(traces) == 1
    trace = traces[0]
    assert trace.violation is True  # a real tool was reachable => boundary action succeeded
    # The audit recording must have been parsed back from the entrypoint.
    assert len(trace.records) == 1
    assert trace.records[0].tool == "search_documents"
    assert trace.records[0].args == {"query": "test"}
