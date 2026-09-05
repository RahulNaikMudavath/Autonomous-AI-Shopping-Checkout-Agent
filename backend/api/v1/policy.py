"""
Phase 5: Purchase Policy & Spending Guardrails API Endpoints
Provides deterministic pre-purchase policy evaluation and policy inspection.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db_session
from backend.domain.marketplace import (
    EvaluatePolicyRequest, PolicyEvaluationResponse, PurchasePolicyDetail
)
from backend.services.policy_engine import PolicyEngine

policy_router = APIRouter(tags=["Purchase Policy & Safety Guardrails"])


@policy_router.post(
    "/policy/evaluate",
    response_model=PolicyEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Checkout Quote Against Policy",
    description="Evaluates an authoritative checkout quote against active spending limits, merchant rules, category restrictions, and security policies without executing payment."
)
def evaluate_policy(
    request: EvaluatePolicyRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: Session = Depends(get_db_session)
) -> PolicyEvaluationResponse:
    effective_session_id = x_session_id or request.session_id
    return PolicyEngine.evaluate_quote_against_policy(
        db=db,
        quote_id=request.quote_id,
        policy_id=request.policy_id,
        caller_session_id=effective_session_id
    )


@policy_router.get(
    "/policy/active",
    response_model=PurchasePolicyDetail,
    summary="Get Active Purchase Policy",
    description="Retrieves the current active purchase policy for the requested scope."
)
def get_active_policy(
    scope: str = Query(default="GLOBAL", description="Policy scope (GLOBAL, USER, SESSION)"),
    scope_id: Optional[str] = Query(default=None, description="Optional scope identifier"),
    db: Session = Depends(get_db_session)
) -> PurchasePolicyDetail:
    policy = PolicyEngine.get_or_create_default_policy(db=db, scope=scope, scope_id=scope_id)
    return PurchasePolicyDetail.model_validate(policy)
