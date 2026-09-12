"""Policy validator"""
import yaml
from pathlib import Path
from typing import List, Tuple
from apcv.core.policy.schema import Policy


class PolicyValidationError(Exception):
    """Policy validation error"""
    def __init__(self, message: str, file_path: str = "", line_no: int = 0):
        self.file_path = file_path
        self.line_no = line_no
        full_msg = message
        if file_path and line_no:
            full_msg = f"{file_path}:{line_no}: {message}"
        super().__init__(full_msg)


class PolicyValidator:
    """Validator for policy YAML files"""

    def validate_file(self, path: str) -> Tuple[bool, List[str]]:
        """
        Validate policy file

        Args:
            path: Path to policy YAML file

        Returns:
            (is_valid, error_list)
        """
        policy_file = Path(path)
        if not policy_file.exists():
            raise FileNotFoundError(f"Policy file not found: {path}")

        try:
            # Load YAML
            with open(policy_file, 'r') as f:
                data = yaml.safe_load(f)

            # Parse as Policy model
            policy = Policy(**data)

            # Validate policy constraints
            errors = policy.validate_policy()

            return len(errors) == 0, errors

        except yaml.YAMLError as e:
            raise PolicyValidationError(f"Invalid YAML: {e}", path, 0)
        except Exception as e:
            raise PolicyValidationError(f"Validation failed: {e}", path, 0)

    def load_policy(self, path: str) -> Policy:
        """Load and validate policy from file"""
        is_valid, errors = self.validate_file(path)
        if not is_valid:
            raise PolicyValidationError(f"Policy validation failed: {errors}", path)

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        return Policy(**data)
