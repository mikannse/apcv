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


class MCPServer(BaseModel):
    """MCP server connection declaration discovered via static analysis.

    Represents an MCP endpoint an agent declares to connect to, NOT the tools
    that server exposes (tool enumeration needs runtime list_tools — route B).
    """
    name: str = Field(..., description="Server name (dict key, or URL, or '<unresolved>')")
    transport: str = Field(
        default="unknown",
        description="Transport: stdio | http | unknown",
    )
    url: str = Field(default="", description="HTTP endpoint URL (http transport)")
    command: str = Field(default="", description="Launch command (stdio transport)")
    args: List[str] = Field(default_factory=list, description="Command args (stdio transport)")
    unresolved: bool = Field(
        default=False,
        description="True if the config referenced a variable and could not be statically resolved",
    )


class SubAgent(BaseModel):
    """A create_agent(...) declaration discovered via static analysis.

    Represents an agent (parent or child) declared in code with its tools list.
    Inheritance chains (who invokes whom) are NOT traced — that is implicit at
    runtime and unreliable to reconstruct statically.
    """
    name: str = Field(default="<unnamed>", description="Assignment variable name, or '<unnamed>'")
    tools: List[str] = Field(default_factory=list, description="Tool names declared in this agent's tools=[...]")
    unresolved: bool = Field(
        default=False,
        description="True if the tools list referenced a variable and could not be statically resolved",
    )


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
    mcp_servers: List[MCPServer] = Field(default_factory=list, description="MCP endpoints declared by the agent")
    sub_agents: List[SubAgent] = Field(default_factory=list, description="create_agent declarations (parent + child) with their tools")


def create_empty_sbom(agent_path: str, framework: str = "langgraph") -> SBOM:
    """Create empty SBOM structure"""
    return SBOM(
        agent_path=agent_path,
        metadata=Metadata(framework=framework)
    )
