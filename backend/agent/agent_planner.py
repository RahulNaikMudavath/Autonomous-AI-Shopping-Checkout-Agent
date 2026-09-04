"""
Phase 3 Step 3: Autonomous AI Shopping Agent - Agent Planner
Generates type-safe, validated ExecutionPlans for shopping goals.
Enforces the PHASE_3_ALLOWED_ACTIONS allowlist and rejects unauthorized actions.
"""
from typing import List, Optional
from backend.domain.agent_schemas import (
    ShoppingIntent, ExecutionPlan, PlanStep, AgentAction,
    PHASE_3_ALLOWED_ACTIONS, AgentPlan, AgentPlanStep
)


class AgentPlanner:
    """
    Creates and validates execution plans for the autonomous shopping agent.
    """

    @classmethod
    def create_plan(cls, intent: ShoppingIntent) -> ExecutionPlan:
        """
        Produces a structured, validated ExecutionPlan from a validated ShoppingIntent.
        """
        if not intent:
            raise ValueError("Intent cannot be None when creating an execution plan.")

        # If the intent is ambiguous or requires clarification
        if intent.is_ambiguous:
            steps = [
                PlanStep(
                    id="step_clarification",
                    action=AgentAction.REQUEST_CLARIFICATION,
                    description=intent.clarification_needed or "Request user clarification for ambiguous requirements",
                    status="PENDING"
                )
            ]
            plan = ExecutionPlan(
                goal=f"Request clarification for ambiguous goal: '{intent.raw_query}'",
                total_steps=1,
                steps=steps,
                status="PLANNED"
            )
            plan.validate_actions()
            return plan

        # Standard multi-step shopping workflow
        budget_desc = f"under ₹{intent.budget_max:,.2f}" if intent.budget_max else "no budget limit"
        steps = [
            PlanStep(
                id="step_discover",
                action=AgentAction.DISCOVER_PRODUCTS,
                description=f"Federated discovery across Amazon, Flipkart, and Croma for {intent.category} ({budget_desc})",
                status="PENDING"
            ),
            PlanStep(
                id="step_normalize",
                action=AgentAction.NORMALIZE_PRODUCTS,
                description="Normalize candidate schemas, pricing decimals, and technical specifications",
                status="PENDING"
            ),
            PlanStep(
                id="step_constraints",
                action=AgentAction.APPLY_CONSTRAINTS,
                description="Apply deterministic hard budget and specification gates",
                status="PENDING"
            ),
            PlanStep(
                id="step_rank",
                action=AgentAction.RANK_PRODUCTS,
                description=f"Multi-criteria decision analysis (MCDA) ranking optimized for {intent.objective.value}",
                status="PENDING"
            ),
            PlanStep(
                id="step_recommend",
                action=AgentAction.GENERATE_RECOMMENDATION,
                description="Synthesize explainable recommendations with verified bullet points and trade-offs",
                status="PENDING"
            ),
            PlanStep(
                id="step_complete",
                action=AgentAction.COMPLETE,
                description="Autonomous shopping workflow execution complete",
                status="PENDING"
            )
        ]

        plan = ExecutionPlan(
            goal=f"Discover, filter, and recommend best {intent.category} for '{intent.raw_query}'",
            total_steps=len(steps),
            steps=steps,
            status="PLANNED"
        )
        plan.validate_actions()
        return plan

    @classmethod
    def validate_action_authorization(cls, action_name: str) -> AgentAction:
        """
        Validates that an action name is authorized within Phase 3.
        Rejects arbitrary actions like 'AUTHORIZE_PAYMENT', 'EXECUTE_SHELL', etc.
        """
        try:
            action = AgentAction(action_name)
        except ValueError:
            raise ValueError(f"Unauthorized or unknown action: '{action_name}'. Allowed actions: {[a.value for a in PHASE_3_ALLOWED_ACTIONS]}")
        
        if action not in PHASE_3_ALLOWED_ACTIONS:
            raise ValueError(f"Action '{action_name}' is not authorized in Phase 3.")
        return action

    @classmethod
    def to_legacy_plan(cls, plan: ExecutionPlan) -> AgentPlan:
        """Converts ExecutionPlan to AgentPlan for backwards compatibility."""
        legacy_steps = [
            AgentPlanStep(
                step_number=idx + 1,
                step_name=step.id,
                agent_or_tool=step.action.value,
                description=step.description,
                status=step.status
            )
            for idx, step in enumerate(plan.steps)
        ]
        return AgentPlan(
            goal=plan.goal,
            total_steps=plan.total_steps,
            steps=legacy_steps
        )
