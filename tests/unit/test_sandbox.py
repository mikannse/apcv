"""Tests for sandbox config translation (pure function, no Docker needed)."""
from apcv.core.execution.sandbox import (
    build_sandbox_config,
    build_docker_run_args,
    classify_denied_paths,
    build_denied_file_mounts,
    DEFAULT_USER,
)
from apcv.core.policy.schema import Policy, Metadata


def _policy(boundaries):
    return Policy(metadata=Metadata(name="test"), boundaries=boundaries)


def test_read_only_policy_maps_to_read_only_sandbox():
    policy = _policy({"filesystem": {"read_only": True}})
    config = build_sandbox_config(policy)
    assert config["read_only"] is True


def test_writable_policy_maps_to_writable_sandbox():
    policy = _policy({"filesystem": {"read_only": False}})
    config = build_sandbox_config(policy)
    assert config["read_only"] is False


def test_network_disabled_maps_to_network_none():
    policy = _policy({"network": {"network_enabled": False}})
    config = build_sandbox_config(policy)
    assert config["network_enabled"] is False


def test_network_enabled_maps_to_bridge():
    policy = _policy({"network": {"network_enabled": True}})
    config = build_sandbox_config(policy)
    assert config["network_enabled"] is True


def test_defaults_when_boundaries_absent():
    policy = _policy({})
    config = build_sandbox_config(policy)
    assert config["read_only"] is False
    assert config["network_enabled"] is False
    assert config["user"] == DEFAULT_USER


def test_docker_run_args_no_network_and_read_only():
    policy = _policy({
        "filesystem": {"read_only": True},
        "network": {"network_enabled": False},
    })
    args = build_docker_run_args(policy, "img", ["/bin/sh", "-c", "echo hi"])
    # Base flags
    assert args[0] == "run"
    assert "--rm" in args
    # Isolation flags
    assert "--network=none" in args
    assert "--read-only" in args
    assert f"--user={DEFAULT_USER}" in args
    # Image then command
    assert args[-4] == "img"
    assert args[-3] == "/bin/sh"
    assert args[-2] == "-c"
    assert args[-1] == "echo hi"


def test_docker_run_args_network_enabled_uses_bridge():
    policy = _policy({"network": {"network_enabled": True}})
    args = build_docker_run_args(policy, "img", ["true"])
    assert "--network=bridge" in args
    assert "--network=none" not in args
    assert "--read-only" not in args


def test_classify_denied_paths_splits_files_and_dirs():
    policy = _policy({"filesystem": {
        "denied_paths": ["/etc/passwd", "/etc/shadow", "/etc", "/root", "/home/u/.aws/credentials"]
    }})
    files, dirs = classify_denied_paths(policy)
    assert files == ["/etc/passwd", "/etc/shadow", "/home/u/.aws/credentials"]
    assert dirs == ["/etc", "/root"]


def test_classify_known_sensitive_files_without_extension():
    policy = _policy({"filesystem": {"denied_paths": ["/etc/shadow", "/etc/sudoers"]}})
    files, dirs = classify_denied_paths(policy)
    assert files == ["/etc/shadow", "/etc/sudoers"]
    assert dirs == []


def test_build_denied_file_mounts_only_includes_files():
    policy = _policy({"filesystem": {
        "denied_paths": ["/etc/passwd", "/etc"]
    }})
    mounts = build_denied_file_mounts(policy)
    assert mounts == ["<EMPTY>:/etc/passwd:ro"]


def test_build_denied_file_mounts_empty_when_no_denied_paths():
    policy = _policy({"filesystem": {"read_only": True}})
    assert build_denied_file_mounts(policy) == []
