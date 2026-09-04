"""
Phase 3 Step 7: Autonomous AI Shopping Agent - Graph Orchestrator
Production-style state graph engine for controlled, explainable agent execution.
Enforces typed tool boundaries, allowed action allowlists, bounded retries, step-level observability,
and strict human authorization boundaries (zero autonomous purchases/orders).
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
import time
from typing import Any, Callable, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session

logger = logging.getLogger("agentcart.agent.graph")

from backend.domain.agent_schemas import (
    ShoppingAgentState, ShoppingIntent, ExecutionPlan, PlanStep,
    AgentAction, PHASE_3_ALLOWED_ACTIONS, AgentTraceStep, NormalizedProductCandidate,
    ShoppingAgentResult, RecommendationResult, RankingResult, RankedProductCandidate,
    ConstraintFilterResult, DiscoveryResult, MerchantDiscoveryStatus
)
from backend.agent.intent_parser import IntentParser
from backend.agent.agent_planner import AgentPlanner
from backend.agent.discovery_service import DiscoveryService
from backend.agent.constraint_engine import ConstraintEngine
from backend.agent.ranking_engine import RankingEngine
from backend.agent.recommendation_engine import RecommendationEngine
from backend.trust_safety.untrusted_content_sanitizer import UntrustedContentSanitizer
from backend.database.models import ShoppingSession, ShoppingTask, AgentRun


class ShoppingAgentGraph:
    """
    Controlled autonomous agent graph orchestrator.
    Flow:
    START -> validate_intent_node -> plan_node -> route_plan -> (clarification | discovery -> apply_constraints -> rank -> recommend -> complete) -> END
    """

    @classmethod
    def create_initial_state(
        cls,
        user_message: str,
        session_id: Optional[str] = None,
        user_id: str = "default_user",
        shopping_intent: Optional[ShoppingIntent] = None
    ) -> ShoppingAgentState:
        """Initializes a new strongly typed agent state."""
        return ShoppingAgentState(
            session_id=session_id or f"sess_{uuid.uuid4().hex[:12]}",
            user_message=user_message,
            user_id=user_id,
            shopping_intent=shopping_intent,
            execution_plan=None,
            current_step_index=0,
            status="PENDING",
            discovered_products=[],
            errors=[],
            retry_count=0,
            max_retries=2,
            trace_id=f"trace_{uuid.uuid4().hex[:16]}",
            trace_steps=[],
            timestamps={"created_at": datetime.now(timezone.utc).isoformat()},
            metadata={"phase": "phase_3_step_7"}
        )

    @classmethod
    def validate_intent_node(cls, state: ShoppingAgentState) -> ShoppingAgentState:
        """
        Step 1: Validates or extracts structured intent from raw user input.
        Sanitizes adversarial instructions and enforces bounds.
        """
        start_time = time.perf_counter()
        try:
            # 1. Security scan
            sanitized_scan = UntrustedContentSanitizer.sanitize_merchant_content(
                raw_text=state.user_message,
                merchant_name="User Query",
                source_field="user_message"
            )
            effective_msg = sanitized_scan.sanitized_clean_content

            if not sanitized_scan.is_safe:
                state.trace_steps.append(AgentTraceStep(
                    step_id="step_security_scan",
                    title="Security Guardrail: Prompt Injection Scan",
                    agent_name="UntrustedContentSanitizer",
                    status="warning",
                    summary=f"Threat detected and neutralized ({sanitized_scan.threat_severity.value}): {', '.join(sanitized_scan.injections_detected)}",
                    details={"is_safe": False, "injections": sanitized_scan.injections_detected},
                    execution_time_ms=1
                ))

            if state.shopping_intent is None:
                intent = IntentParser.parse_intent(effective_msg)
                state.shopping_intent = intent

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            state.trace_steps.append(AgentTraceStep(
                step_id="step_intent_validation",
                title="Intent Extraction & Validation",
                agent_name="IntentParser",
                status="completed",
                summary=f"Extracted goal for '{state.shopping_intent.category}' (is_ambiguous={state.shopping_intent.is_ambiguous})",
                details={
                    "category": state.shopping_intent.category,
                    "budget_max": str(state.shopping_intent.budget_max) if state.shopping_intent.budget_max else None,
                    "quantity": state.shopping_intent.quantity,
                    "is_ambiguous": state.shopping_intent.is_ambiguous
                },
                execution_time_ms=elapsed_ms
            ))
            state.status = "VALIDATED"
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            state.errors.append(f"INTENT_INVALID: {str(e)}")
            state.status = "FAILED"
            state.trace_steps.append(AgentTraceStep(
                step_id="step_intent_validation",
                title="Intent Extraction & Validation",
                agent_name="IntentParser",
                status="failed",
                summary=f"Intent validation failed: {str(e)}",
                execution_time_ms=elapsed_ms
            ))
        return state

    @classmethod
    def plan_node(cls, state: ShoppingAgentState) -> ShoppingAgentState:
        """
        Step 2: Constructs a bounded execution plan enforcing PHASE_3_ALLOWED_ACTIONS.
        """
        if state.status == "FAILED" or state.shopping_intent is None:
            return state

        start_time = time.perf_counter()
        try:
            plan = AgentPlanner.create_plan(state.shopping_intent)
            plan.validate_actions()
            state.execution_plan = plan
            state.status = "PLANNING"
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            state.trace_steps.append(AgentTraceStep(
                step_id="step_planning",
                title="Execution Plan Generation",
                agent_name="AgentPlanner",
                status="completed",
                summary=f"Generated {plan.total_steps}-step DAG for '{plan.goal}'",
                details={
                    "total_steps": plan.total_steps,
                    "actions": [s.action.value for s in plan.steps]
                },
                execution_time_ms=elapsed_ms
            ))
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            state.errors.append(f"PLAN_INVALID: {str(e)}")
            state.status = "FAILED"
            state.trace_steps.append(AgentTraceStep(
                step_id="step_planning",
                title="Execution Plan Generation",
                agent_name="AgentPlanner",
                status="failed",
                summary=f"Plan construction failed: {str(e)}",
                execution_time_ms=elapsed_ms
            ))
        return state

    @classmethod
    def route_plan_node(cls, state: ShoppingAgentState) -> str:
        """
        Conditional Router: Decides next graph edge based on state and plan.
        """
        if state.status == "FAILED" or not state.execution_plan:
            return "failure"
        if state.shopping_intent and state.shopping_intent.is_ambiguous:
            return "clarification"
        if state.execution_plan.steps and state.execution_plan.steps[0].action == AgentAction.DISCOVER_PRODUCTS:
            return "discovery"
        return "complete"

    @classmethod
    def clarification_node(cls, state: ShoppingAgentState) -> ShoppingAgentState:
        """Handles ambiguous requests by halting at clarification boundary."""
        state.status = "CLARIFICATION_REQUIRED"
        if state.execution_plan and state.execution_plan.steps:
            state.execution_plan.steps[0].status = "COMPLETED"

        clarification_msg = (
            state.shopping_intent.clarification_needed
            if state.shopping_intent and state.shopping_intent.clarification_needed
            else "Please provide more details regarding your category and maximum budget."
        )
        state.metadata["clarification_prompt"] = clarification_msg

        state.trace_steps.append(AgentTraceStep(
            step_id="step_clarification",
            title="Clarification Boundary Reached",
            agent_name="AgentGraph",
            status="completed",
            summary=f"Halted at clarification boundary: {clarification_msg}",
            details={"clarification_prompt": clarification_msg},
            execution_time_ms=1
        ))
        return state

    @classmethod
    def discovery_node(
        cls,
        state: ShoppingAgentState,
        db: Optional[Session] = None
    ) -> ShoppingAgentState:
        """
        Step 3: Executes typed federated multi-merchant discovery across Amazon, Flipkart, Croma.
        Uses bounded retry logic and logs execution metrics.
        """
        if state.status == "FAILED" or not state.shopping_intent:
            return state

        start_time = time.perf_counter()
        retries = 0
        success = False
        candidates: List[NormalizedProductCandidate] = []
        discovery_res: Optional[DiscoveryResult] = None

        # Ensure active db session
        if db is None:
            from backend.database.session import get_db_session
            sess_gen = get_db_session()
            active_db = next(sess_gen)
        else:
            active_db = db

        while retries <= state.max_retries and not success:
            try:
                discovery_res = DiscoveryService.discover(
                    db=active_db,
                    intent=state.shopping_intent,
                    page_size=20
                )
                candidates = discovery_res.products
                state.metadata["discovery_merchants_attempted"] = discovery_res.merchants_attempted
                state.metadata["discovery_merchants_succeeded"] = discovery_res.merchants_succeeded
                state.metadata["discovery_merchants_failed"] = discovery_res.merchants_failed
                state.metadata["discovery_partial_results"] = discovery_res.partial_results
                state.metadata["discovery_statuses"] = [s.model_dump(mode="json") for s in discovery_res.merchant_statuses]
                state.metadata["discovery_result"] = discovery_res
                success = True
            except Exception as e:
                retries += 1
                state.retry_count = retries
                if retries > state.max_retries:
                    state.errors.append(f"DISCOVERY_FAILED after {retries} retries: {str(e)}")
                    state.status = "FAILED"
                    break

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        state.discovered_products = candidates

        if success and discovery_res:
            state.status = "DISCOVERING"
            if state.execution_plan:
                disc_step = next((s for s in state.execution_plan.steps if s.action == AgentAction.DISCOVER_PRODUCTS), None)
                if disc_step:
                    disc_step.status = "COMPLETED"
                    disc_step.execution_time_ms = elapsed_ms
                norm_step = next((s for s in state.execution_plan.steps if s.action == AgentAction.NORMALIZE_PRODUCTS), None)
                if norm_step:
                    norm_step.status = "COMPLETED"
                    norm_step.execution_time_ms = 1

            state.trace_steps.append(AgentTraceStep(
                step_id="step_discovery",
                title="Federated Multi-Merchant Discovery",
                agent_name="DiscoveryService",
                status="completed",
                summary=f"Discovered {len(candidates)} normalized products across {len(discovery_res.merchants_succeeded)} merchants",
                details={
                    "candidates_count": len(candidates),
                    "canonical_count": len(discovery_res.canonical_products),
                    "merchants_succeeded": discovery_res.merchants_succeeded,
                    "merchants_failed": discovery_res.merchants_failed,
                    "partial_results": discovery_res.partial_results,
                    "retries": retries
                },
                execution_time_ms=elapsed_ms
            ))
        else:
            state.trace_steps.append(AgentTraceStep(
                step_id="step_discovery",
                title="Federated Multi-Merchant Discovery",
                agent_name="DiscoveryService",
                status="failed",
                summary=f"Discovery failed: {state.errors[-1] if state.errors else 'Unknown'}",
                execution_time_ms=elapsed_ms
            ))
        return state

    @classmethod
    def apply_hard_constraints_node(cls, state: ShoppingAgentState) -> ShoppingAgentState:
        """
        Step 4: Deterministic Hard-Constraint Filtering.
        Filters discovered products against non-negotiable budget bounds, stock availability,
        and technical specification minimums. Zero LLM involvement.
        """
        if state.status == "FAILED" or not state.shopping_intent:
            return state

        start_time = time.perf_counter()
        try:
            filter_res = ConstraintEngine.filter_products(
                candidates=state.discovered_products,
                intent=state.shopping_intent
            )
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            # Retain only passing candidates in state
            state.discovered_products = filter_res.passed_candidates
            state.metadata["constraint_filtering"] = {
                "total_input": filter_res.total_input,
                "total_passed": filter_res.total_passed,
                "total_rejected": filter_res.total_rejected,
                "rejection_summary": filter_res.rejection_summary,
                "execution_time_ms": elapsed_ms
            }
            state.metadata["constraint_result"] = filter_res

            if state.execution_plan:
                cons_step = next((s for s in state.execution_plan.steps if s.action == AgentAction.APPLY_CONSTRAINTS), None)
                if cons_step:
                    cons_step.status = "COMPLETED"
                    cons_step.execution_time_ms = elapsed_ms

            state.trace_steps.append(AgentTraceStep(
                step_id="step_hard_constraints",
                title="Deterministic Hard-Constraint Filtering",
                agent_name="ConstraintEngine",
                status="completed",
                summary=f"Filtered {filter_res.total_input} candidates: {filter_res.total_passed} passed, {filter_res.total_rejected} rejected",
                details={
                    "total_input": filter_res.total_input,
                    "passed_count": filter_res.total_passed,
                    "rejected_count": filter_res.total_rejected,
                    "rejection_summary": filter_res.rejection_summary
                },
                execution_time_ms=elapsed_ms
            ))
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            state.errors.append(f"CONSTRAINT_FILTER_FAILED: {str(e)}")
            state.trace_steps.append(AgentTraceStep(
                step_id="step_hard_constraints",
                title="Deterministic Hard-Constraint Filtering",
                agent_name="ConstraintEngine",
                status="failed",
                summary=f"Constraint filtering failed: {str(e)}",
                execution_time_ms=elapsed_ms
            ))
        return state

    @classmethod
    def rank_products_node(cls, state: ShoppingAgentState) -> ShoppingAgentState:
        """
        Step 5: Deterministic Multi-Criteria Decision Analysis (MCDA) Ranking.
        Scores passing candidates across technical specs, price efficiency, delivery speed,
        ratings, discounts, and inventory health. Zero LLM involvement.
        """
        if state.status == "FAILED" or not state.shopping_intent:
            return state

        start_time = time.perf_counter()
        try:
            rank_res = RankingEngine.rank_products(
                candidates=state.discovered_products,
                intent=state.shopping_intent
            )
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            # Store ranking result metadata
            state.metadata["ranking"] = {
                "total_candidates": rank_res.total_candidates,
                "best_overall_id": rank_res.best_overall.candidate.id if rank_res.best_overall else None,
                "best_overall_score": rank_res.best_overall.overall_score if rank_res.best_overall else None,
                "best_value_id": rank_res.best_value.candidate.id if rank_res.best_value else None,
                "fastest_delivery_id": rank_res.fastest_delivery.candidate.id if rank_res.fastest_delivery else None,
                "scoring_profile": rank_res.scoring_profile,
                "weights_applied": rank_res.weights_applied,
                "execution_time_ms": elapsed_ms
            }
            state.metadata["ranking_result"] = rank_res

            # Update ordered discovered products list
            state.discovered_products = [item.candidate for item in rank_res.ranked_products]

            if state.execution_plan:
                rank_step = next((s for s in state.execution_plan.steps if s.action == AgentAction.RANK_PRODUCTS), None)
                if rank_step:
                    rank_step.status = "COMPLETED"
                    rank_step.execution_time_ms = elapsed_ms

            top_title = rank_res.best_overall.candidate.title if rank_res.best_overall else "None"
            top_score = rank_res.best_overall.overall_score if rank_res.best_overall else 0.0
            state.trace_steps.append(AgentTraceStep(
                step_id="step_mcda_ranking",
                title="Deterministic MCDA Ranking",
                agent_name="RankingEngine",
                status="completed",
                summary=f"Ranked {rank_res.total_candidates} candidates. Top pick: '{top_title[:40]}' (Score: {top_score:.1f}/100)",
                details={
                    "total_ranked": rank_res.total_candidates,
                    "best_overall": top_title,
                    "top_score": top_score,
                    "best_value": rank_res.best_value.candidate.title if rank_res.best_value else None,
                    "fastest_delivery": rank_res.fastest_delivery.candidate.title if rank_res.fastest_delivery else None,
                    "weights": rank_res.weights_applied
                },
                execution_time_ms=elapsed_ms
            ))
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            state.errors.append(f"RANKING_FAILED: {str(e)}")
            state.trace_steps.append(AgentTraceStep(
                step_id="step_mcda_ranking",
                title="Deterministic MCDA Ranking",
                agent_name="RankingEngine",
                status="failed",
                summary=f"Ranking failed: {str(e)}",
                execution_time_ms=elapsed_ms
            ))
        return state

    @classmethod
    def generate_recommendation_node(cls, state: ShoppingAgentState) -> ShoppingAgentState:
        """
        Step 6: Explainable Recommendation Synthesis.
        Transforms deterministic ranking, constraint audits, and discovery coverage
        into structured, verifiable recommendations with side-by-side comparison.
        """
        if state.status == "FAILED":
            return state

        start_time = time.perf_counter()
        try:
            ranking_result: Optional[RankingResult] = state.metadata.get("ranking_result")
            constraint_result: Optional[ConstraintFilterResult] = state.metadata.get("constraint_result")
            discovery_result: Optional[DiscoveryResult] = state.metadata.get("discovery_result")

            rec_result = RecommendationEngine.build_recommendation_result(
                ranking_result=ranking_result,
                constraint_result=constraint_result,
                discovery_result=discovery_result,
                intent=state.shopping_intent,
                session_id=state.session_id,
                metadata=state.metadata
            )
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            state.metadata["recommendation_result"] = rec_result

            if state.execution_plan:
                rec_step = next((s for s in state.execution_plan.steps if s.action == AgentAction.GENERATE_RECOMMENDATION), None)
                if rec_step:
                    rec_step.status = "COMPLETED"
                    rec_step.execution_time_ms = elapsed_ms

            if rec_result.best_overall:
                top_c = rec_result.best_overall.candidate
                state.trace_steps.append(AgentTraceStep(
                    step_id="step_recommendation",
                    title="Explainable Recommendation Synthesis",
                    agent_name="RecommendationEngine",
                    status="completed",
                    summary=f"Synthesized Top Pick: '{top_c.title[:40]}' on {top_c.merchant_name} (₹{top_c.current_price:,.2f}) with {len(rec_result.alternatives)} alternatives",
                    details={
                        "top_pick": top_c.title,
                        "merchant": top_c.merchant_name,
                        "price": str(top_c.current_price),
                        "overall_score": rec_result.best_overall.overall_score,
                        "alternatives_count": len(rec_result.alternatives)
                    },
                    execution_time_ms=elapsed_ms
                ))
            elif state.status == "CLARIFICATION_REQUIRED":
                state.trace_steps.append(AgentTraceStep(
                    step_id="step_recommendation",
                    title="Recommendation Clarification Required",
                    agent_name="RecommendationEngine",
                    status="completed",
                    summary=state.metadata.get("clarification_prompt", "Clarification needed before recommendations can be synthesized."),
                    details={"clarification_needed": True},
                    execution_time_ms=elapsed_ms
                ))
            else:
                state.status = "NO_MATCH"
                state.trace_steps.append(AgentTraceStep(
                    step_id="step_recommendation",
                    title="Explainable Recommendation: No Matching Products",
                    agent_name="RecommendationEngine",
                    status="completed",
                    summary=f"Zero products satisfied all hard constraints. Rejection summary: {rec_result.rejection_summary}",
                    details={"rejection_summary": rec_result.rejection_summary},
                    execution_time_ms=elapsed_ms
                ))
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            state.errors.append(f"RECOMMENDATION_FAILED: {str(e)}")
            state.trace_steps.append(AgentTraceStep(
                step_id="step_recommendation",
                title="Explainable Recommendation Synthesis",
                agent_name="RecommendationEngine",
                status="failed",
                summary=f"Recommendation synthesis failed: {str(e)}",
                execution_time_ms=elapsed_ms
            ))
        return state

    @classmethod
    def complete_node(cls, state: ShoppingAgentState) -> ShoppingAgentState:
        """Finalizes graph execution and sets completion state."""
        if state.status not in ("FAILED", "CLARIFICATION_REQUIRED", "NO_MATCH"):
            state.status = "COMPLETED"
            if state.execution_plan:
                state.execution_plan.status = "COMPLETED"
        state.timestamps["completed_at"] = datetime.now(timezone.utc).isoformat()
        return state

    @classmethod
    def run_graph(
        cls,
        user_message: str,
        db: Optional[Session] = None,
        session_id: Optional[str] = None,
        user_id: str = "default_user",
        shopping_intent: Optional[ShoppingIntent] = None
    ) -> ShoppingAgentState:
        """
        Executes the controlled autonomous shopping agent state graph from START to END.
        """
        # 1. Initialize State
        state = cls.create_initial_state(
            user_message=user_message,
            session_id=session_id,
            user_id=user_id,
            shopping_intent=shopping_intent
        )

        # 2. Node 1: Validate Intent
        state = cls.validate_intent_node(state)

        # 3. Node 2: Plan
        state = cls.plan_node(state)

        # 4. Conditional Edge: Route
        route = cls.route_plan_node(state)

        if route == "clarification":
            state = cls.clarification_node(state)
            state = cls.generate_recommendation_node(state)
            state = cls.complete_node(state)
        elif route == "discovery":
            state = cls.discovery_node(state, db=db)
            state = cls.apply_hard_constraints_node(state)
            state = cls.rank_products_node(state)
            state = cls.generate_recommendation_node(state)
            state = cls.complete_node(state)
        elif route == "failure":
            state.status = "FAILED"
            state.timestamps["failed_at"] = datetime.now(timezone.utc).isoformat()
        else:
            state = cls.generate_recommendation_node(state)
            state = cls.complete_node(state)

        # 5. Optional DB Session Persistence
        if db is not None:
            try:
                cls._persist_session_state(db=db, state=state)
            except Exception:
                pass  # Avoid breaking graph if session record fails

        return state

    @classmethod
    def run_shopping_agent(
        cls,
        user_message: str,
        db: Optional[Session] = None,
        session_id: Optional[str] = None,
        user_id: str = "default_user",
        scoring_profile: str = "default_v1",
        shopping_intent: Optional[ShoppingIntent] = None
    ) -> ShoppingAgentResult:
        """
        Primary application-level entry point returning a strongly typed ShoppingAgentResult.
        Hides internal LangGraph, database, and merchant adapter implementation details.
        """
        start_time = time.perf_counter()
        
        # Ensure active db session
        if db is None:
            from backend.database.session import get_db_session
            sess_gen = get_db_session()
            active_db = next(sess_gen)
        else:
            active_db = db

        # Run State Graph
        state = cls.run_graph(
            user_message=user_message,
            db=active_db,
            session_id=session_id,
            user_id=user_id,
            shopping_intent=shopping_intent
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        # Reconstruct typed RecommendationResult
        rec_result: Optional[RecommendationResult] = state.metadata.get("recommendation_result")
        if rec_result is None:
            ranking_result = state.metadata.get("ranking_result")
            constraint_result = state.metadata.get("constraint_result")
            discovery_result = state.metadata.get("discovery_result")
            rec_result = RecommendationEngine.build_recommendation_result(
                ranking_result=ranking_result,
                constraint_result=constraint_result,
                discovery_result=discovery_result,
                intent=state.shopping_intent,
                session_id=state.session_id,
                metadata=state.metadata
            )

        # Determine top-level status
        if state.status == "FAILED":
            final_status = "FAILED"
        elif state.status == "CLARIFICATION_REQUIRED":
            final_status = "NEEDS_CLARIFICATION"
        elif state.status == "NO_MATCH" or (rec_result and not rec_result.best_overall and rec_result.data_completeness == "EMPTY"):
            final_status = "NO_MATCH"
        elif state.metadata.get("discovery_partial_results", False):
            final_status = "PARTIAL_RESULTS"
        else:
            final_status = "COMPLETED"

        warnings: List[str] = list(rec_result.warnings) if rec_result else []
        if state.metadata.get("discovery_partial_results") and "PARTIAL_MERCHANT_RESULTS" not in " ".join(warnings):
            warnings.append("PARTIAL_MERCHANT_RESULTS: One or more merchant catalogs failed to respond.")

        # Clarification and suggested action
        clarification_prompt = None
        suggested_action = None
        if final_status == "NEEDS_CLARIFICATION":
            clarification_prompt = state.metadata.get("clarification_prompt") or (
                state.shopping_intent.clarification_needed if state.shopping_intent else "Please clarify your budget or category."
            )
            suggested_action = "Provide maximum budget or specific product category to refine search."
        elif final_status == "NO_MATCH":
            suggested_action = "Consider increasing your budget ceiling or relaxing minimum hardware specifications."

        # Discovery summary
        discovery_summary = {
            "total_candidates": len(state.discovered_products),
            "merchants_attempted": state.metadata.get("discovery_merchants_attempted", []),
            "merchants_succeeded": state.metadata.get("discovery_merchants_succeeded", []),
            "merchants_failed": state.metadata.get("discovery_merchants_failed", []),
            "partial_results": state.metadata.get("discovery_partial_results", False)
        }

        # Constraint summary
        constraint_summary = state.metadata.get("constraint_filtering", {})

        # Ranking summary
        ranking_summary = state.metadata.get("ranking", {})

        # Execution metadata
        exec_metadata = {
            "execution_time_ms": elapsed_ms,
            "scoring_profile": scoring_profile,
            "trace_id": state.trace_id,
            "retry_count": state.retry_count,
            "completed_at": state.timestamps.get("completed_at", datetime.now(timezone.utc).isoformat())
        }

        # Persist session and task records if database session is provided
        if db is not None:
            cls._persist_session_state(db, state)

        return ShoppingAgentResult(
            session_id=state.session_id,
            status=final_status,
            query=user_message,
            intent=state.shopping_intent,
            execution_plan=state.execution_plan,
            discovery_summary=discovery_summary,
            constraint_summary=constraint_summary,
            ranking_summary=ranking_summary,
            recommendation=rec_result,
            warnings=warnings,
            errors=state.errors,
            clarification_prompt=clarification_prompt,
            suggested_action=suggested_action,
            execution_metadata=exec_metadata,
            trace=state.trace_steps,
            requires_human_authorization=rec_result.requires_human_authorization if rec_result else False
        )

    @classmethod
    def _persist_session_state(cls, db: Session, state: ShoppingAgentState) -> None:
        """Persists state metrics into PostgreSQL ShoppingSession and ShoppingTask tables."""
        try:
            from backend.services.session_service import SessionService
            user_id = state.user_id or "default_user"
            SessionService.ensure_user(db, user_id)

            existing_sess = db.query(ShoppingSession).filter(ShoppingSession.id == state.session_id).first()
            if not existing_sess:
                new_sess = ShoppingSession(
                    id=state.session_id,
                    user_id=user_id,
                    title=state.user_message[:100],
                    status=state.status
                )
                db.add(new_sess)
                db.commit()

            # Record task
            task = ShoppingTask(
                session_id=state.session_id,
                raw_prompt=state.user_message,
                status=state.status,
                extracted_constraints=state.shopping_intent.model_dump(mode="json") if state.shopping_intent else {},
                execution_plan=state.execution_plan.model_dump(mode="json") if state.execution_plan else []
            )
            db.add(task)
            db.commit()
        except Exception as e:
            logger.warning("Failed to persist session/task state to PostgreSQL: %s", str(e))
            db.rollback()


# Module-level convenience function
def run_shopping_agent(
    user_message: str,
    db: Optional[Session] = None,
    session_id: Optional[str] = None,
    user_id: str = "default_user",
    scoring_profile: str = "default_v1",
    shopping_intent: Optional[ShoppingIntent] = None
) -> ShoppingAgentResult:
    """Convenience functional entry point for autonomous shopping agent execution."""
    return ShoppingAgentGraph.run_shopping_agent(
        user_message=user_message,
        db=db,
        session_id=session_id,
        user_id=user_id,
        scoring_profile=scoring_profile,
        shopping_intent=shopping_intent
    )
