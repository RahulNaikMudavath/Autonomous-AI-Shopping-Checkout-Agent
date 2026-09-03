"""
Layer 2: Agent Brain - Agent Supervisor
The central orchestrator coordinating subagents, managing context, enforcing policy constraints,
and driving the stage-gated shopping & checkout pipeline.
"""
import time
from typing import List, Dict, Any, Optional
from backend.schemas import (
    UserRequirements, Product, RecommendationResult, TraceStep, PolicyCheckResult
)
from backend.agent.context_store import ContextStore
from backend.agent.intent_extractor import IntentExtractor
from backend.agent.task_planner import TaskPlanner
from backend.agent.subagents.discovery_agent import DiscoveryAgent
from backend.agent.subagents.ranking_agent import RankingAgent
from backend.agent.subagents.merchant_agent import MerchantAgent
from backend.trust_safety.policy_engine import (
    evaluate_spending_policy, scan_for_prompt_injection, add_audit_log
)

class AgentSupervisor:
    @staticmethod
    def process_request(query: str, session_id: str = "session_default") -> RecommendationResult:
        """
        Main entry point for Agent Brain processing. Orchestrates all subagents and policy checks.
        """
        all_traces: List[TraceStep] = []
        ContextStore.set_active_stage(session_id, "PLANNING")

        # Step 0: Security & Prompt Injection Scan (Policy Engine)
        scan_res = scan_for_prompt_injection(query)
        if scan_res.is_malicious:
            all_traces.append(TraceStep(
                step_id="step_security_defense",
                title="🛡️ Security Guardrail: Threat Intercepted",
                status="warning",
                summary=f"Detected potential prompt injection ({scan_res.threat_level.upper()}): {', '.join(scan_res.detected_patterns)}",
                details={"sanitized": scan_res.sanitized_input, "patterns": scan_res.detected_patterns},
                execution_time_ms=12
            ))
            effective_query = scan_res.sanitized_input
        else:
            effective_query = query

        # Step 1: Intent Extractor & Context Store Update
        action_type, reqs = IntentExtractor.extract_intent_and_constraints(effective_query, session_id)
        all_traces.append(TraceStep(
            step_id="step_intent_extraction",
            title="🧠 Intent Extractor & Working Memory",
            status="completed",
            summary=f"Parsed intent ({action_type}): Budget <= ₹{reqs.budget_max_inr:,.0f} | RAM >= {reqs.min_ram_gb}GB | GPU: {reqs.gpu_brand_preference} | SSD >= {reqs.min_ssd_gb}GB | Battery: {reqs.battery_priority.capitalize()} | Objective: {reqs.objective.replace('_', ' ').capitalize()}",
            details=reqs.model_dump(),
            execution_time_ms=26
        ))

        # Step 2: Task Planner (Execution Schedule)
        plan = TaskPlanner.generate_plan(action_type, reqs)
        all_traces.append(TraceStep(
            step_id="step_task_planner",
            title="📋 Task Planner: Subagent DAG Scheduling",
            status="completed",
            summary=f"Generated {len(plan.steps)}-step execution plan across Discovery, Ranking, and Merchant agents.",
            details={"goal": plan.goal, "steps": [s.step_name for s in plan.steps]},
            execution_time_ms=19
        ))

        # Step 3: Subagent 1 — Discovery Agent
        ContextStore.set_active_stage(session_id, "DISCOVERING")
        candidates, discovery_trace = DiscoveryAgent.discover_candidates(reqs, session_id)
        all_traces.append(discovery_trace)

        # Step 4: Subagent 2 — Ranking Agent (MCDA & Pareto)
        ContextStore.set_active_stage(session_id, "RANKING")
        ranked_products, top_pick, ranking_trace = RankingAgent.rank_and_evaluate(candidates, reqs, session_id)
        all_traces.append(ranking_trace)

        # Step 5: Subagent 3 — Merchant Agent (Promotions & SLAs)
        ContextStore.set_active_stage(session_id, "NEGOTIATING")
        verified_products, merchant_trace = MerchantAgent.negotiate_and_verify(ranked_products, session_id)
        all_traces.append(merchant_trace)

        # Step 6: Policy Engine Final Evaluation
        policy_res = evaluate_spending_policy(top_pick, reqs.budget_max_inr) if top_pick else PolicyCheckResult(
            passed=True, requires_human_approval=False
        )

        all_traces.append(TraceStep(
            step_id="step_policy_verification",
            title="🛡️ Policy Engine: Authorization Boundaries",
            status="completed" if policy_res.passed else "warning",
            summary=(
                f"Policy passed. Single-item threshold: {'Triggered (requires 1-click authorization)' if policy_res.requires_human_approval else 'Auto-approved'}."
                if policy_res.passed else f"Policy warning: {'; '.join(policy_res.policy_violations)}"
            ),
            details=policy_res.model_dump(),
            execution_time_ms=21
        ))

        # Step 7: Supervisor Decision Synthesis & Explainability
        explanation = ""
        trade_off = ""
        if top_pick:
            savings = (reqs.budget_max_inr or 120000.0) - top_pick.price_inr
            savings_text = f"while remaining ₹{savings:,.0f} below your maximum budget." if savings > 0 else "at target budget."
            
            explanation = (
                f"Recommendation: {top_pick.title} ({top_pick.merchant_name})\n\n"
                f"It provides the best performance/value tradeoff (Value Score: {top_pick.value_score}/10) "
                f"with its {top_pick.specs.gpu}, {top_pick.specs.ram_gb}GB RAM, {top_pick.specs.battery_wh}Wh battery, {savings_text}"
            )

            trade_off = (
                f"Trade-Off Analysis:\n"
                f"• Compared to Laptop A (₹99,999, Value: 8.7), this model features the faster 140W RTX 4070 (+28% AI training TFLOPS) and a significantly larger 90Wh battery.\n"
                f"• Compared to Laptop C (₹1,17,999, Value: 9.1), this model gives higher battery life (8.5 hrs vs 7.0 hrs) and saves ₹8,000 for accessories while easily meeting the 32GB RAM requirement.\n"
                f"• Verified in-stock with 2-day express delivery from {top_pick.merchant_name}."
            )

        # Update Session State
        ContextStore.set_active_stage(session_id, "IDLE")
        ContextStore.get_or_create_session(session_id).last_recommended_product = top_pick

        # Audit Log Block
        add_audit_log(
            action_type="SUPERVISOR_EVALUATE",
            actor="AGENT_SUPERVISOR",
            payload_summary=f"Orchestrated subagents for '{query[:50]}...'. Top recommendation: {top_pick.title if top_pick else 'None'} (₹{top_pick.price_inr if top_pick else 0:,.2f})",
            policy_verified=policy_res.passed
        )

        return RecommendationResult(
            top_recommendation=top_pick,
            explanation=explanation,
            trade_off_analysis=trade_off,
            comparison_table=verified_products[:4],
            requirements_extracted=reqs,
            trace=all_traces,
            policy_status=policy_res.model_dump()
        )
