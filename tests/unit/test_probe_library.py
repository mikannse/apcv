"""Tests for probe library"""
import pytest
from apcv.core.probes.library import ProbeLibrary


@pytest.fixture
def library():
    return ProbeLibrary()


def test_library_loads_probes(library):
    """Test library loads all probes"""
    assert library.get_total_count() >= 20
    assert library.get_total_count() <= 35


def test_library_has_all_categories(library):
    """Test library has probes from all categories"""
    assert len(library.get_probes_by_category("filesystem")) >= 6
    assert len(library.get_probes_by_category("tool")) >= 5
    assert len(library.get_probes_by_category("privilege")) >= 4
    assert len(library.get_probes_by_category("network")) >= 4
    assert len(library.get_probes_by_category("rate_limit")) >= 2


def test_library_get_probe_by_id(library):
    """Test retrieving probe by ID"""
    probe = library.get_probe_by_id("fs_read_1")
    assert probe is not None
    assert probe.id == "fs_read_1"


def test_library_no_duplicate_ids(library):
    """Test no duplicate probe IDs"""
    ids = [p.id for p in library.probes]
    assert len(ids) == len(set(ids))


def test_library_probes_valid_format(library):
    """Test all probes have valid format"""
    for probe in library.probes:
        assert probe.id
        assert probe.category
        assert probe.description
        assert probe.test_command
        assert probe.expected_outcome
        assert probe.severity in ["critical", "high", "medium", "low"]
