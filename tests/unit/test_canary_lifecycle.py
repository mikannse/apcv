"""Tests for the canary sentinel lifecycle (setup/check)."""
import pytest

import apcv.core.execution.canary as canary_mod


@pytest.fixture(autouse=True)
def _isolate_canary_dir(tmp_path, monkeypatch):
    """Redirect the /canary sentinel dir into tmp_path so tests don't touch /."""
    monkeypatch.setattr(canary_mod, "CANARY_DIR", str(tmp_path))
    monkeypatch.setattr(canary_mod, "EXEC_MARKER", tmp_path / "marker")
    monkeypatch.setattr(canary_mod, "WRITE_MARKER", tmp_path / "out")
    monkeypatch.setattr(canary_mod, "READ_SENTINEL", tmp_path / "secret")


def test_code_exec_not_triggered_initially():
    canary_mod.setup_canary("code_exec")
    assert canary_mod.check_canary("code_exec", {}, []) is False


def test_code_exec_triggered_when_marker_created():
    canary_mod.setup_canary("code_exec")
    canary_mod.EXEC_MARKER.write_text("x")
    assert canary_mod.check_canary("code_exec", {}, []) is True


def test_file_write_triggered_when_out_created():
    canary_mod.setup_canary("file_write")
    assert canary_mod.check_canary("file_write", {}, []) is False
    canary_mod.WRITE_MARKER.write_text("x")
    assert canary_mod.check_canary("file_write", {}, []) is True


def test_file_read_seeds_token_and_detects_in_result():
    canary_mod.setup_canary("file_read")
    assert canary_mod.READ_SENTINEL.read_text() == canary_mod.READ_TOKEN
    assert canary_mod.check_canary("file_read", {}, ["some output"]) is False
    assert canary_mod.check_canary(
        "file_read", {}, [f"got {canary_mod.READ_TOKEN} here"]
    ) is True


def test_file_read_detects_token_in_any_result():
    canary_mod.setup_canary("file_read")
    results = ["a", "b", f"contains {canary_mod.READ_TOKEN}"]
    assert canary_mod.check_canary("file_read", {}, results) is True


def test_setup_clears_previous_marker():
    canary_mod.setup_canary("code_exec")
    canary_mod.EXEC_MARKER.write_text("x")
    # re-setup must clear the marker
    canary_mod.setup_canary("code_exec")
    assert canary_mod.EXEC_MARKER.exists() is False
