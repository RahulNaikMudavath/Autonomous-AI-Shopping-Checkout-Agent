"""
Layer 2: Agent Brain - Task Planner
Constructs structured execution DAGs and coordinates subagent execution order.
"""
from typing import List, Dict, Any
from pydantic import BaseModel
from backend.schemas import UserRequirements

class PlanStep(BaseModel):
    step_name: str
    assigned_agent: str  # "Supervisor", "DiscoveryAgent", "RankingAgent", "MerchantAgent", "PolicyEngine"
    description: str
    dependencies: List[str] = []
    is_critical: bool = True

class ExecutionPlan(BaseModel):
    plan_id: str
    goal: str
    steps: List[PlanStep]

class TaskPlanner:
    @staticmethod
    def generate_plan(action_type: str, reqs: UserRequirements) -> ExecutionPlan:
        """
        Creates an optimal subagent task schedule based on intent and constraints.
        """
        steps = []

        # Step 1: Policy Pre-Check
        steps.append(PlanStep(
            step_name="POLICY_PRE_CHECK",
            assigned_agent="PolicyEngine",
            description="Scan query for prompt injections and evaluate spending bounds",
            dependencies=[]
        ))

        # Step 2: Discovery
        steps.append(PlanStep(
            step_name="DISCOVERY_FEDERATED",
            assigned_agent="DiscoveryAgent",
            description="Parallel multi-merchant broadcast & spec attribute normalization",
            dependencies=["POLICY_PRE_CHECK"]
        ))

        # Step 3: Ranking
        steps.append(PlanStep(
            step_name="RANKING_MCDA",
            assigned_agent="RankingAgent",
            description="Compute Multi-Criteria Decision Analysis scores & Pareto-optimal tradeoff set",
            dependencies=["DISCOVERY_FEDERATED"]
        ))

        # Step 4: Merchant Negotiation & Terms
        steps.append(PlanStep(
            step_name="MERCHANT_VERIFICATION",
            assigned_agent="MerchantAgent",
            description="Verify merchant trust scores, apply active coupon codes & check express logistics",
            dependencies=["RANKING_MCDA"]
        ))

        # Step 5: Supervisor Synthesis
        steps.append(PlanStep(
            step_name="SUPERVISOR_SYNTHESIS",
            assigned_agent="Supervisor",
            description="Synthesize explainable recommendation & formulate autonomous action choices",
            dependencies=["MERCHANT_VERIFICATION"]
        ))

        # If Direct Purchase is requested
        if action_type == "DIRECT_PURCHASE":
            steps.append(PlanStep(
                step_name="EXECUTE_STAGE_GATE_CHECKOUT",
                assigned_agent="Supervisor",
                description="Trigger Cart -> Checkout -> Authorization -> Payment -> Order pipeline",
                dependencies=["SUPERVISOR_SYNTHESIS"]
            ))

        return ExecutionPlan(
            plan_id=f"plan_{reqs.objective}_{int(reqs.budget_max_inr or 0)}",
            goal=f"Identify best laptop for {reqs.target_use_case} within ₹{reqs.budget_max_inr:,.0f}",
            steps=steps
        )
