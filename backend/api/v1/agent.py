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
    ShoppingIntent, RecommendationResponse, AgentPlan,
    AgentIntentRequest, AgentIntentResponse,
    AgentSessionRequest, AgentSessionResponse, ExecutionPlan
)
from backend.agent.intent_parser import IntentParser
from backend.agent.workflow_planner import WorkflowPlanner
from backend.agent.agent_planner import AgentPlanner
from backend.agent.agent_runner import ShoppingAgentRunner
from backend.agent.agent_graph import ShoppingAgentGraph

agent_router = APIRouter(prefix="/agent", tags=["Autonomous Shopping Agent"])


class AgentQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language shopping request")
    session_id: Optional[str] = Field(default=None, description="Optional active shopping session ID")
    user_id: str = Field(default="default_user", description="User identity")


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
    "/sessions",
    response_model=AgentSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Start Agent Shopping Session & Execution Graph",
    description="Initializes an agent session, extracts intent, generates safe execution plan, and executes federated discovery."
)
def start_agent_session(
    request: AgentSessionRequest,
    db: Session = Depends(get_db_session)
) -> AgentSessionResponse:
    query_text = request.get_message_text()
    state = ShoppingAgentGraph.run_graph(
        user_message=query_text,
        db=db,
        session_id=request.session_id,
        user_id=request.user_id
    )
    return AgentSessionResponse(
        session_id=state.session_id,
        status=state.status,
        intent=state.shopping_intent,
        plan=state.execution_plan,
        discovered_count=len(state.discovered_products),
        trace=state.trace_steps,
        errors=state.errors,
        latency_ms=sum(t.execution_time_ms for t in state.trace_steps)
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
    query_text = request.get_query_text()
    return IntentParser.parse_intent(
        query=query_text,
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
