"""Integration tests for isolated agent-probe execution (requires Docker).

Skipped when the Docker daemon is unavailable. Marked with `docker` so they can
be excluded with `pytest -m "not docker"`.
"""
import pytest

from apcv.core.execution.executor import IsolatedExecutor
from apcv.core.policy.schema import Policy, Metadata
from apcv.core.probes.probe import Probe


pytestmark = pytest.mark.docker


def _policy(**boundaries):
    return Policy(metadata=Metadata(name="test"), boundaries=boundaries)


def _agent_probe(**kwargs):
    base = dict(
        id="probe_x",
        category="tool",
        description="d",
        test_command="agent.call_tool('search_documents', {'query': 'test'})",
        expected_outcome="recorded",
        execution="agent",
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


def test_agent_probe_captures_tool_records(executor):
    """A tool-calling agent probe produces audit records on the trace."""
    agent = "tests/fixtures/sample_agents/simple_agent.py"
    traces = executor.execute_agent_probes([_agent_probe()], agent, _policy())

    assert len(traces) == 1
    trace = traces[0]
    assert trace.violation is True  # a real tool was reachable => boundary action succeeded
    # The audit recording must have been parsed back from the entrypoint.
    assert len(trace.records) == 1
    assert trace.records[0].tool == "search_documents"
    assert trace.records[0].args == {"query": "test"}


def test_agent_probe_undeclared_tool_is_not_violation(executor):
    """An undeclared tool is correctly rejected (not a violation)."""
    agent = "tests/fixtures/sample_agents/simple_agent.py"
    probe = _agent_probe(
        id="undeclared",
        test_command="agent.call_tool('not_a_real_tool', {})",
    )
    traces = executor.execute_agent_probes([probe], agent, _policy())

    assert len(traces) == 1
    assert traces[0].violation is False


def test_parallel_agent_probes_return_all(executor):
    agent = "tests/fixtures/sample_agents/simple_agent.py"
    probes = [
        _agent_probe(id="p1"),
        _agent_probe(id="p2", test_command="agent.call_tool('nope', {})"),
    ]
    traces = executor.execute_agent_probes(probes, agent, _policy())
    assert len(traces) == 2
    assert {t.probe_id for t in traces} == {"p1", "p2"}
