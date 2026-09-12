"""Web UI - FastAPI backend"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="APCV Web UI", version="0.1.0")


class AgentReport(BaseModel):
    name: str
    compliance_score: int
    verdict: str
    tools_count: int


class DashboardData(BaseModel):
    agents: List[AgentReport]
    overall_score: float


@app.get("/api/dashboard")
def get_dashboard() -> DashboardData:
    """Get dashboard data"""
    return DashboardData(
        agents=[
            AgentReport(
                name="github-agent",
                compliance_score=95,
                verdict="PASS",
                tools_count=5
            )
        ],
        overall_score=95.0
    )


@app.get("/api/agents/{agent_id}")
def get_agent(agent_id: str):
    """Get agent details"""
    return {
        "id": agent_id,
        "compliance_score": 95,
        "violations": []
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
