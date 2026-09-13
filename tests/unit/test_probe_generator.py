"""Tests for probe generator (agent probes only)."""
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


def test_generator_limited_tools_policy(generator):
    """A tool allow-list yields tool (agent) probes."""
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

    tool_probes = [p for p in probes if p.category == "tool"]
    assert len(tool_probes) > 0
    # All generated probes are agent-category (no shell probes).
    assert all(p.execution == "agent" for p in probes)


def test_generator_rate_limit_policy(generator):
    """A rate-limit boundary yields rate_limit probes."""
    policy = Policy(
        metadata=Metadata(name="Rated"),
        boundaries={"rate_limit": {"calls_per_minute": 10}}
    )

    probes = generator.generate(policy)
    assert any(p.category == "rate_limit" for p in probes)
    assert all(p.execution == "agent" for p in probes)


def test_generator_no_duplicates(generator):
    policy = Policy(
        metadata=Metadata(name="Complex"),
        boundaries={
            "tool": {"allowed_tools": ["search"], "denied_tools": []},
            "rate_limit": {"calls_per_minute": 10},
        }
    )

    probes = generator.generate(policy)
    ids = [p.id for p in probes]
    assert len(ids) == len(set(ids))


def test_generator_empty_policy_yields_no_probes(generator):
    """No tool/rate boundary => no agent probes (no shell probes anymore)."""
    policy = Policy(metadata=Metadata(name="Empty"), boundaries={})
    assert generator.generate(policy) == []


def test_generator_never_generates_shell_probes(generator):
    """Filesystem/network/privilege boundaries must NOT yield shell probes."""
    policy = Policy(
        metadata=Metadata(name="ReadOnly"),
        boundaries={
            "filesystem": {"read_only": True, "allowed_paths": ["/tmp"], "denied_paths": []},
            "network": {"network_enabled": False, "allowed_domains": [], "denied_domains": []},
        }
    )
    probes = generator.generate(policy)
    assert all(p.execution == "agent" for p in probes)
