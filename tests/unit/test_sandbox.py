"""Tests for sandbox translation (pure function, no Docker needed).

The sandbox is a FIXED isolation cage, not a policy enforcer. These tests
assert that build_docker_run_args always produces the same isolation posture
(non-root + no network) regardless of the declared policy.
"""
from apcv.core.execution.sandbox import build_docker_run_args, DEFAULT_USER
from apcv.core.policy.schema import Policy, Metadata


def _policy(boundaries):
    return Policy(metadata=Metadata(name="test"), boundaries=boundaries)


def test_always_runs_non_root():
    args = build_docker_run_args(_policy({}), "img", ["true"])
    assert f"--user={DEFAULT_USER}" in args


def test_always_disables_network():
    args = build_docker_run_args(_policy({}), "img", ["true"])
    assert "--network=none" in args
    assert "--network=bridge" not in args


def test_network_is_fixed_regardless_of_policy():
    # Even if the policy declares network_enabled, the sandbox stays isolated.
    policy = _policy({"network": {"network_enabled": True}})
    args = build_docker_run_args(policy, "img", ["true"])
    assert "--network=none" in args


def test_policy_does_not_change_isolation():
    # A policy with lots of constraints must NOT alter the sandbox posture.
    policy = _policy({
        "filesystem": {"read_only": True, "denied_paths": ["/etc/passwd"]},
        "network": {"network_enabled": False},
    })
    args = build_docker_run_args(policy, "img", ["true"])
    # No denied-path mounts, no read-only flag — the sandbox does not enforce.
    assert not any("--read-only" in a for a in args)
    assert not any("-v" == a for a in args)


def test_image_and_command_appended():
    args = build_docker_run_args(_policy({}), "img", ["/bin/sh", "-c", "echo hi"])
    assert args[-4] == "img"
    assert args[-3:] == ["/bin/sh", "-c", "echo hi"]


def test_entrypoint_override():
    args = build_docker_run_args(
        _policy({}), "img", ["-c", "echo hi"], entrypoint="/bin/sh"
    )
    assert "--entrypoint" in args
    assert "/bin/sh" in args
