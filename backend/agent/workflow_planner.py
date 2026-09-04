"""
Phase 3: Autonomous AI Shopping Agent - Workflow Planner
Constructs structured multi-step execution plans and DAG schedules for shopping goals.
"""
from typing import List
from backend.domain.agent_schemas import ShoppingIntent, AgentPlan, AgentPlanStep


class WorkflowPlanner:
    """
    Generates deterministic execution plans for autonomous shopping runs.
    """

    @classmethod
    def generate_plan(cls, intent: ShoppingIntent) -> AgentPlan:
        """
        Creates the standard 7-step autonomous shopping pipeline DAG.
        """
        steps = [
            AgentPlanStep(
                step_number=1,
                step_name="Intent Extraction & Unit Normalization",
                agent_or_tool="IntentParser",
                description=f"Extracted goal for '{intent.category}' (Max Budget: ₹{intent.budget_max:,.2f} | Objective: {intent.objective.value})" if intent.budget_max else f"Extracted goal for '{intent.category}'",
                status="COMPLETED"
            ),
            AgentPlanStep(
                step_number=2,
                step_name="Security Guardrail & Injection Scan",
                agent_or_tool="UntrustedContentSanitizer",
                description="Scans query and untrusted merchant descriptions to prevent indirect prompt injections",
                status="COMPLETED"
            ),
            AgentPlanStep(
                step_number=3,
                step_name="Federated Multi-Merchant Discovery",
                agent_or_tool="CatalogTools.search_multi_merchant_catalog",
                description="Queries Amazon India, Flipkart, and Croma catalogs in parallel",
                status="PENDING"
            ),
            AgentPlanStep(
                step_number=4,
                step_name="Universal Product Normalization",
                agent_or_tool="ProductNormalizer",
                description="Normalizes specifications, stock availability, and merchant shipping tiers",
                status="PENDING"
            ),
            AgentPlanStep(
                step_number=5,
                step_name="Deterministic Hard Constraint Filtering",
                agent_or_tool="ConstraintEngine",
                description=f"Applies non-negotiable budget (<= ₹{intent.budget_max:,.2f}) and technical specification gates" if intent.budget_max else "Applies technical specification gates",
                status="PENDING"
            ),
            AgentPlanStep(
                step_number=6,
                step_name="MCDA Multi-Criteria Ranking",
                agent_or_tool="RankingEngine",
                description=f"Scores candidates across performance, price efficiency, delivery, and rating for {intent.objective.value}",
                status="PENDING"
            ),
            AgentPlanStep(
                step_number=7,
                step_name="Explainable Recommendation & Authorization Gate",
                agent_or_tool="RecommendationEngine",
                description="Synthesizes Top Pick, Best Value, Fastest Delivery, and prepares human authorization boundary",
                status="PENDING"
            ),
        ]

        return AgentPlan(
            goal=f"Discover, evaluate, and recommend best {intent.category} for '{intent.raw_query}'",
            total_steps=len(steps),
            steps=steps
        )
