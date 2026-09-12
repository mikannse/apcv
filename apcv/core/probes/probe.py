"""Probe data model"""
from pydantic import BaseModel, Field


class Probe(BaseModel):
    """Security test probe"""
    id: str = Field(..., description="Unique probe ID (e.g., 'fs_read_1')")
    category: str = Field(
        ...,
        description="Probe category",
        pattern="^(filesystem|tool|privilege|network|sub_agent|parameter|rate_limit)$"
    )
    description: str = Field(..., description="Human-readable description")
    test_command: str = Field(..., description="Command to execute")
    expected_outcome: str = Field(..., description="Expected outcome of probe")
    severity: str = Field(
        default="high",
        description="Severity level",
        pattern="^(critical|high|medium|low)$"
    )


def create_probe(
    probe_id: str,
    category: str,
    description: str,
    test_command: str,
    expected_outcome: str,
    severity: str = "high"
) -> Probe:
    """Helper to create probe"""
    return Probe(
        id=probe_id,
        category=category,
        description=description,
        test_command=test_command,
        expected_outcome=expected_outcome,
        severity=severity
    )
