"""SBOM (Software Bill of Materials) data models"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ToolParameter(BaseModel):
    """Tool parameter definition"""
    name: str = Field(..., description="Parameter name")
    type: str = Field(default="str", description="Parameter type")
    required: bool = Field(default=False, description="Is parameter required")
    default: Optional[Any] = Field(default=None, description="Default value")


class Tool(BaseModel):
    """Tool definition in SBOM"""
    id: str = Field(..., description="Unique tool ID")
    name: str = Field(..., description="Tool name")
    module: str = Field(..., description="Module containing the tool")
    parameters: List[ToolParameter] = Field(default_factory=list)
    return_type: str = Field(default="Any", description="Return type")
    description: str = Field(default="", description="Tool description")


class Metadata(BaseModel):
    """SBOM metadata"""
    framework: str = Field(..., description="Framework name (e.g., 'langgraph')")
    framework_version: str = Field(default="", description="Framework version")
    python_version: str = Field(default="", description="Python version")


class SBOM(BaseModel):
    """Software Bill of Materials for an Agent"""
    model_config = ConfigDict(validate_assignment=True)

    version: str = Field(default="1.0", description="SBOM format version")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_path: str = Field(..., description="Path to Agent code")
    metadata: Metadata
    tools: List[Tool] = Field(default_factory=list)


def create_empty_sbom(agent_path: str, framework: str = "langgraph") -> SBOM:
    """Create empty SBOM structure"""
    return SBOM(
        agent_path=agent_path,
        metadata=Metadata(framework=framework)
    )
