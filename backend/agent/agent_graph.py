"""
Phase 3 Step 3: Autonomous AI Shopping Agent - Graph Orchestrator
Production-style state graph engine for controlled agent execution.
Enforces typed tool boundaries, allowed action allowlists, bounded retries, and step-level observability.
"""
from datetime import datetime, timezone
import time
from typing import Any, Callable, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session

from backend.domain.agent_schemas import (
    ShoppingAgentState, ShoppingIntent, ExecutionPlan, PlanStep,
    AgentAction, PHASE_3_ALLOWED_ACTIONS, AgentTraceStep, NormalizedProductCandidate
)
from backend.agent.intent_parser import IntentParser
from backend.agent.agent_planner import AgentPlanner
from backend.agent.tools.catalog_tools import CatalogTools
from backend.trust_safety.untrusted_content_sanitizer import UntrustedContentSanitizer
from backend.database.models import ShoppingSession, ShoppingTask, AgentRun


class ShoppingAgentGraph:
    """
    Controlled autonomous agent graph orchestrator.
    Flow:
    START -> validate_intent_node -> plan_node -> route_plan -> (clarification | discovery -> complete) -> END
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
            metadata={"phase": "phase_3_step_3"}
        )

    @classmethod
    def validate_intent_node(cls, state: ShoppingAgentState) -> ShoppingAgentState:
        """
        Step 1: Validates or extracts structured intent from raw user input.
        Sanitizes adversarial instructions and enforces bounds.
        """
        start_time = time.perf_counter()
        try:
            if state.shopping_intent is None:
                intent = IntentParser.parse_intent(state.user_message)
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

        # Ensure active db session
        if db is None:
            from backend.database.session import get_db_session
            sess_gen = get_db_session()
            active_db = next(sess_gen)
        else:
            active_db = db

        while retries <= state.max_retries and not success:
            try:
                from backend.agent.discovery_service import DiscoveryService
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

        if success:
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
            from backend.agent.constraint_engine import ConstraintEngine
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
    def complete_node(cls, state: ShoppingAgentState) -> ShoppingAgentState:
        """Finalizes graph execution and sets completion state."""
        if state.status != "FAILED" and state.status != "CLARIFICATION_REQUIRED":
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
        elif route == "discovery":
            state = cls.discovery_node(state, db=db)
            state = cls.apply_hard_constraints_node(state)
            state = cls.complete_node(state)
        elif route == "failure":
            state.status = "FAILED"
            state.timestamps["failed_at"] = datetime.now(timezone.utc).isoformat()
        else:
            state = cls.complete_node(state)

        # 5. Optional DB Session Persistence
        if db is not None:
            try:
                cls._persist_session_state(db=db, state=state)
            except Exception:
                pass  # Avoid breaking graph if session record fails

        return state

    @classmethod
    def _persist_session_state(cls, db: Session, state: ShoppingAgentState) -> None:
        """Persists state metrics into PostgreSQL ShoppingSession and ShoppingTask tables."""
        existing_sess = db.query(ShoppingSession).filter(ShoppingSession.id == state.session_id).first()
        if not existing_sess:
            new_sess = ShoppingSession(
                id=state.session_id,
                user_id=state.user_id,
                title=state.user_message[:100],
                status=state.status
            )
            db.add(new_sess)
            db.commit()

        # Record task
        task = ShoppingTask(
            session_id=state.session_id,
            task_type="AUTONOMOUS_SHOPPING_PLAN",
            status=state.status,
            intent_json=state.shopping_intent.model_dump(mode="json") if state.shopping_intent else None,
            execution_plan_json=state.execution_plan.model_dump(mode="json") if state.execution_plan else None,
            candidates_discovered=len(state.discovered_products)
        )
        db.add(task)
        db.commit()
