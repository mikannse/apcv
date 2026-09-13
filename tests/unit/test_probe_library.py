"""Tests for probe library (agent-category probes only)."""
import pytest
from apcv.core.probes.library import ProbeLibrary


@pytest.fixture
def library():
    return ProbeLibrary()


def test_library_loads_agent_probes(library):
    """Library holds only agent-category probes (tool + rate_limit)."""
    assert library.get_total_count() >= 7
    # tool (7) + rate_limit (3) = 10 agent probes.
    assert library.get_total_count() == 10


def test_library_has_only_agent_categories(library):
    assert len(library.get_probes_by_category("tool")) >= 5
    assert len(library.get_probes_by_category("rate_limit")) >= 2
    # Shell categories are gone.
    assert library.get_probes_by_category("filesystem") == []
    assert library.get_probes_by_category("network") == []
    assert library.get_probes_by_category("privilege") == []


def test_library_get_probe_by_id(library):
    probe = library.get_probe_by_id("tool_undeclared_1")
    assert probe is not None
    assert probe.id == "tool_undeclared_1"
    assert probe.execution == "agent"


def test_library_no_duplicate_ids(library):
    ids = [p.id for p in library.probes]
    assert len(ids) == len(set(ids))


def test_library_all_probes_are_agent_execution(library):
    for probe in library.probes:
        assert probe.execution == "agent"
        assert probe.id
        assert probe.category
        assert probe.description
        assert probe.test_command
        assert probe.expected_outcome
        assert probe.severity in ["critical", "high", "medium", "low"]
