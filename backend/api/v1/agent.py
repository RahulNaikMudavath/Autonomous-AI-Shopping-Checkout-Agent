"""
Phase 3: Autonomous AI Shopping Agent API Endpoints (v1)
Exposes REST endpoints for:
- POST /api/v1/agent/query (End-to-end autonomous shopping pipeline)
- POST /api/v1/agent/intent (Intent extraction & unit normalization)
- POST /api/v1/agent/plan (Multi-step agent workflow planning)
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.session import get_db_session
from backend.domain.agent_schemas import (
    ShoppingIntent, RecommendationResponse, AgentPlan
)
from backend.agent.intent_parser import IntentParser
from backend.agent.workflow_planner import WorkflowPlanner
from backend.agent.agent_runner import ShoppingAgentRunner

agent_router = APIRouter(prefix="/agent", tags=["Autonomous Shopping Agent"])


class AgentQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language shopping request")
    session_id: Optional[str] = Field(default=None, description="Optional active shopping session ID")
    user_id: str = Field(default="default_user", description="User identity")


class AgentIntentRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language shopping prompt")
    previous_intent: Optional[ShoppingIntent] = Field(default=None, description="Previous turn intent for refinement")


@agent_router.post(
    "/query",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Autonomous Shopping Agent",
    description="Transforms a natural-language shopping goal into structured intent, federates multi-merchant discovery, applies hard constraints, ranks candidates using MCDA, and generates explainable recommendations."
)
def run_autonomous_shopping_agent(
    request: AgentQueryRequest,
    db: Session = Depends(get_db_session)
) -> RecommendationResponse:
    return ShoppingAgentRunner.run_shopping_pipeline(
        db=db,
        query=request.query,
        session_id=request.session_id,
        user_id=request.user_id
    )


@agent_router.post(
    "/intent",
    response_model=ShoppingIntent,
    status_code=status.HTTP_200_OK,
    summary="Extract Structured Shopping Intent",
    description="Parses natural-language user query into normalized constraints, budget decimals, and soft preferences."
)
def extract_shopping_intent(
    request: AgentIntentRequest
) -> ShoppingIntent:
    return IntentParser.parse_intent(
        query=request.query,
        previous_intent=request.previous_intent
    )


@agent_router.post(
    "/plan",
    response_model=AgentPlan,
    status_code=status.HTTP_200_OK,
    summary="Generate Agent Execution Plan",
    description="Produces a step-gated multi-agent execution DAG for a shopping goal."
)
def generate_agent_plan(
    intent: ShoppingIntent
) -> AgentPlan:
    return WorkflowPlanner.generate_plan(intent)
