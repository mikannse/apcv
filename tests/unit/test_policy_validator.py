"""Tests for policy validator"""
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from apcv.core.policy.validator import PolicyValidator, PolicyValidationError


@pytest.fixture
def validator():
    return PolicyValidator()


@pytest.fixture
def valid_policy_yaml():
    return """
metadata:
  name: "Test Policy"
  version: "1.0"
  description: "Test policy"

boundaries:
  tool:
    allowed_tools:
      - search
      - get_issue
    denied_tools: []
"""


def test_validator_accepts_valid_policy(validator, valid_policy_yaml):
    """Test validator accepts valid policy"""
    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(valid_policy_yaml)
        f.flush()
        path = f.name

    try:
        is_valid, errors = validator.validate_file(path)
        assert is_valid is True
        assert len(errors) == 0
    finally:
        Path(path).unlink()


def test_validator_rejects_nonexistent_file(validator):
    """Test validator rejects nonexistent file"""
    with pytest.raises(FileNotFoundError):
        validator.validate_file("/nonexistent/path.yaml")


def test_validator_rejects_invalid_yaml(validator):
    """Test validator rejects invalid YAML"""
    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content:")
        f.flush()
        path = f.name

    try:
        with pytest.raises(PolicyValidationError):
            validator.validate_file(path)
    finally:
        Path(path).unlink()


def test_validator_load_policy(validator, valid_policy_yaml):
    """Test validator can load policy"""
    with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(valid_policy_yaml)
        f.flush()
        path = f.name

    try:
        policy = validator.load_policy(path)
        assert policy.metadata.name == "Test Policy"
    finally:
        Path(path).unlink()
