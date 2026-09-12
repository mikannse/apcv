"""Tests for probe generator"""
import pytest
from apcv.core.probes.library import ProbeLibrary
from apcv.core.probes.generator import ProbeGenerator
from apcv.core.policy.schema import Policy, Metadata


@pytest.fixture
def library():
    return ProbeLibrary()


@pytest.fixture
def generator(library):
    return ProbeGenerator(library)


def test_generator_read_only_policy(generator):
    """Test generator creates write probes for read-only policy"""
    policy = Policy(
        metadata=Metadata(name="Read-Only"),
        boundaries={
            "filesystem": {
                "read_only": True,
                "allowed_paths": ["/tmp"],
                "denied_paths": []
            }
        }
    )

    probes = generator.generate(policy)

    # Should include filesystem probes
    fs_probes = [p for p in probes if p.category == "filesystem"]
    assert len(fs_probes) > 0


def test_generator_limited_tools_policy(generator):
    """Test generator creates tool probes for limited tools policy"""
    policy = Policy(
        metadata=Metadata(name="Limited Tools"),
        boundaries={
            "tool": {
                "allowed_tools": ["search", "get_issue"],
                "denied_tools": []
            }
        }
    )

    probes = generator.generate(policy)

    # Should include tool probes
    tool_probes = [p for p in probes if p.category == "tool"]
    assert len(tool_probes) > 0


def test_generator_no_duplicates(generator):
    """Test generator doesn't create duplicate probes"""
    policy = Policy(
        metadata=Metadata(name="Complex"),
        boundaries={
            "filesystem": {"read_only": True, "allowed_paths": [], "denied_paths": []},
            "tool": {"allowed_tools": ["search"], "denied_tools": []},
            "network": {"network_enabled": False, "allowed_domains": [], "denied_domains": []},
        }
    )

    probes = generator.generate(policy)

    # Check no duplicates
    ids = [p.id for p in probes]
    assert len(ids) == len(set(ids))


def test_generator_privilege_always_included(generator):
    """Test generator always includes privilege probes"""
    policy = Policy(
        metadata=Metadata(name="Minimal"),
        boundaries={}
    )

    probes = generator.generate(policy)

    # Should still include privilege probes
    priv_probes = [p for p in probes if p.category == "privilege"]
    assert len(priv_probes) > 0
