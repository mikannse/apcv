"""Tests for policy schema"""
import pytest
from apcv.core.policy.schema import Policy, Metadata, ToolBoundary, FilesystemBoundary


def test_policy_creation():
    """Test policy creation"""
    policy = Policy(
        metadata=Metadata(name="Test Policy"),
        boundaries={
            "tool": {
                "allowed_tools": ["search", "get_issue"],
                "denied_tools": []
            }
        }
    )
    assert policy.metadata.name == "Test Policy"


def test_tool_boundary_duplicate_detection():
    """Test tool boundary detects duplicates"""
    with pytest.raises(ValueError):
        ToolBoundary(
            allowed_tools=["search", "search"],
            denied_tools=[]
        )


def test_tool_boundary_conflict_detection():
    """Test tool boundary detects conflicts"""
    tb = ToolBoundary(
        allowed_tools=["search", "get_issue"],
        denied_tools=["get_issue"]
    )
    errors = tb.validate()
    assert len(errors) > 0
    assert "get_issue" in str(errors)


def test_filesystem_boundary():
    """Test filesystem boundary"""
    fb = FilesystemBoundary(
        allowed_paths=["/tmp", "/var/tmp"],
        read_only=True
    )
    assert fb.read_only is True
    assert "/tmp" in fb.allowed_paths
