"""Policy DSL schema and validation models"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class Metadata(BaseModel):
    """Policy metadata"""
    name: str = Field(..., description="Policy name")
    version: str = Field(default="1.0", description="Policy version")
    description: str = Field(default="", description="Policy description")
    author: str = Field(default="", description="Policy author")
    tags: List[str] = Field(default_factory=list, description="Policy tags")


class ToolBoundary(BaseModel):
    """Tool usage boundary"""
    allowed_tools: List[str] = Field(default_factory=list)
    denied_tools: List[str] = Field(default_factory=list)

    @field_validator('allowed_tools', 'denied_tools')
    @classmethod
    def check_no_duplicates(cls, v: List[str]) -> List[str]:
        if len(v) != len(set(v)):
            raise ValueError("Duplicate tools not allowed")
        return v

    def validate(self) -> List[str]:
        """Check for conflicts"""
        errors = []
        allowed = set(self.allowed_tools)
        denied = set(self.denied_tools)
        overlap = allowed & denied
        if overlap:
            errors.append(f"Tools in both allowed and denied: {overlap}")
        return errors


class FilesystemBoundary(BaseModel):
    """Filesystem access boundary"""
    allowed_paths: List[str] = Field(default_factory=list)
    denied_paths: List[str] = Field(default_factory=list)
    read_only: bool = Field(default=False)


class NetworkBoundary(BaseModel):
    """Network access boundary"""
    network_enabled: bool = Field(default=False)
    allowed_domains: List[str] = Field(default_factory=list)
    denied_domains: List[str] = Field(default_factory=list)


class ParameterConstraint(BaseModel):
    """Parameter constraint for a tool"""
    tool: str
    parameter: str
    allowed_values: Optional[List[str]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None


class ParameterBoundary(BaseModel):
    """Parameter constraints boundary"""
    constraints: List[ParameterConstraint] = Field(default_factory=list)


class Policy(BaseModel):
    """Complete policy definition"""
    model_config = ConfigDict(validate_assignment=True)

    metadata: Metadata
    boundaries: Dict[str, Any] = Field(default_factory=dict)

    def validate_policy(self) -> List[str]:
        """Validate policy constraints"""
        errors = []
        if "tool" in self.boundaries:
            tb = ToolBoundary(**self.boundaries["tool"])
            errors.extend(tb.validate())
        return errors
