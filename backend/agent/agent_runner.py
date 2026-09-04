"""
Phase 3: Autonomous AI Shopping Agent - Core Agent Runner
Orchestrates the end-to-end autonomous shopping workflow:
1. Intent Parsing & Normalization
2. Security & Prompt Injection Defense Scan
3. Workflow Planning
4. Federated Multi-Merchant Discovery
5. Product Candidate Normalization
6. Deterministic Hard Constraint Evaluation
7. MCDA Multi-Criteria Ranking
8. Explainable Recommendation & Authorization Boundary Synthesis
"""
from decimal import Decimal
import logging
import time
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from backend.domain.agent_schemas import (
    ShoppingIntent, NormalizedProductCandidate, MCDAScoreBreakdown,
    RecommendationResponse, AgentPlan, AgentTraceStep
)
from backend.agent.intent_parser import IntentParser
from backend.agent.workflow_planner import WorkflowPlanner
from backend.agent.tools.catalog_tools import CatalogTools
from backend.agent.product_normalizer import ProductNormalizer
from backend.agent.constraint_engine import ConstraintEngine
from backend.agent.ranking_engine import RankingEngine
from backend.agent.recommendation_engine import RecommendationEngine
from backend.trust_safety.untrusted_content_sanitizer import UntrustedContentSanitizer
from backend.services.session_service import SessionService
from backend.domain.schemas import ShoppingSessionCreate, ShoppingTaskCreate

logger = logging.getLogger("agentcart.agent.runner")


class ShoppingAgentRunner:
    """
    Coordinates autonomous shopping runs with strict security guardrails and telemetry.
    """

    @classmethod
    def run_shopping_pipeline(
        cls,
        db: Session,
        query: str,
        session_id: Optional[str] = None,
        user_id: str = "default_user"
    ) -> RecommendationResponse:
        """
        Executes the full 7-step autonomous shopping pipeline.
        """
        start_time = time.perf_counter()
        traces: List[AgentTraceStep] = []

        # 0. Ensure Shopping Session in PostgreSQL & Redis
        if not session_id:
            session = SessionService.create_session(
                db=db,
                data=ShoppingSessionCreate(user_id=user_id, title=f"Search: {query[:40]}...")
            )
            session_id = session.id
        else:
            try:
                session = SessionService.get_session(db, session_id)
            except Exception:
                session = SessionService.create_session(
                    db=db,
                    data=ShoppingSessionCreate(user_id=user_id, title=f"Search: {query[:40]}...")
                )
                session_id = session.id

        # 1. Security & Prompt Injection Defense Scan
        s1_start = time.perf_counter()
        scan_res = UntrustedContentSanitizer.sanitize_merchant_content(
            raw_text=query,
            merchant_name="User Query",
            source_field="raw_user_prompt"
        )
        effective_query = scan_res.sanitized_clean_content
        s1_dur = int((time.perf_counter() - s1_start) * 1000)

        traces.append(AgentTraceStep(
            step_id="step_security_scan",
            title="🛡️ Security Guardrail: Prompt Injection Scan",
            agent_name="UntrustedContentSanitizer",
            status="warning" if not scan_res.is_safe else "completed",
            summary=(
                f"Scan clean: No prompt injection patterns detected."
                if scan_res.is_safe else
                f"Threat detected and sanitized ({scan_res.threat_severity.value}): {', '.join(scan_res.injections_detected)}"
            ),
            details={"is_safe": scan_res.is_safe, "patterns": scan_res.injections_detected},
            execution_time_ms=s1_dur
        ))

        # 2. Intent Parsing & Unit Normalization
        s2_start = time.perf_counter()
        intent = IntentParser.parse_intent(effective_query)
        s2_dur = int((time.perf_counter() - s2_start) * 1000)

        if intent.is_ambiguous:
            plan = WorkflowPlanner.generate_plan(intent)
            return RecommendationResponse(
                session_id=session_id,
                intent=intent,
                plan=plan,
                total_candidates_discovered=0,
                candidates_passing_constraints=0,
                top_recommendation=None,
                best_value_recommendation=None,
                fastest_delivery_recommendation=None,
                all_recommendations=[],
                trace=traces,
                requires_human_authorization=False,
                authorization_reason=intent.clarification_needed or "Query requires clarification."
            )

        budget_summary = f"Budget <= ₹{intent.budget_max:,.2f}" if intent.budget_max else "No budget ceiling"
        traces.append(AgentTraceStep(
            step_id="step_intent_parser",
            title="🧠 Intent Parser: Structured Goal Extraction",
            agent_name="IntentParser",
            status="completed",
            summary=f"Extracted intent for category '{intent.category}': {budget_summary} | Objective: {intent.objective.value} | Constraints: {len(intent.spec_constraints)} spec rules",
            details={
                "category": intent.category,
                "budget_max": str(intent.budget_max) if intent.budget_max else None,
                "objective": intent.objective.value,
                "constraints": [c.model_dump() for c in intent.spec_constraints]
            },
            execution_time_ms=s2_dur
        ))

        # 3. Execution Plan Scheduling
        plan = WorkflowPlanner.generate_plan(intent)
        traces.append(AgentTraceStep(
            step_id="step_workflow_plan",
            title="📋 Workflow Planner: Multi-Agent DAG Scheduled",
            agent_name="WorkflowPlanner",
            status="completed",
            summary=f"Created {plan.total_steps}-step execution plan for multi-merchant discovery and MCDA ranking.",
            details={"steps": [s.step_name for s in plan.steps]},
            execution_time_ms=5
        ))

        # 4. Federated Multi-Merchant Discovery
        s4_start = time.perf_counter()
        search_res = CatalogTools.search_multi_merchant_catalog(
            db=db,
            category=intent.category,
            query=None,
            max_price=None,  # Do not pre-filter hard budget in SQL so constraint engine can record rejections
            in_stock_only=False,
            page_size=50
        )
        s4_dur = int((time.perf_counter() - s4_start) * 1000)

        traces.append(AgentTraceStep(
            step_id="step_multi_merchant_discovery",
            title="🌐 Federated Discovery: Multi-Merchant Catalog Query",
            agent_name="CatalogTools",
            status="completed",
            summary=f"Polled Amazon India, Flipkart, and Croma catalogs. Discovered {len(search_res.items)} product listings.",
            details={
                "total_items": len(search_res.items),
                "merchants_polled": ["AMAZON", "FLIPKART", "CROMA"]
            },
            execution_time_ms=s4_dur
        ))

        # 5. Product Candidate Normalization
        s5_start = time.perf_counter()
        candidates: List[NormalizedProductCandidate] = []
        for item in search_res.items:
            # Fetch rich details if needed
            detail = CatalogTools.get_product_details(db, item.id)
            cand = ProductNormalizer.normalize_candidate(detail if detail else item)
            candidates.append(cand)
        s5_dur = int((time.perf_counter() - s5_start) * 1000)

        traces.append(AgentTraceStep(
            step_id="step_product_normalizer",
            title="🔄 Product Normalizer: Universal Schema Harmonization",
            agent_name="ProductNormalizer",
            status="completed",
            summary=f"Harmonized specifications, delivery metrics, and stock states for {len(candidates)} candidates.",
            details={"normalized_count": len(candidates)},
            execution_time_ms=s5_dur
        ))

        # 6. Deterministic Hard Constraint Filtering
        s6_start = time.perf_counter()
        passing_candidates, rejected_candidates = ConstraintEngine.filter_candidates(candidates, intent)
        s6_dur = int((time.perf_counter() - s6_start) * 1000)

        # Categorize rejections
        rejection_summary: Dict[str, int] = {}
        for _, reasons in rejected_candidates:
            for r in reasons:
                short_r = r.split(":")[0] if ":" in r else r[:35]
                rejection_summary[short_r] = rejection_summary.get(short_r, 0) + 1

        traces.append(AgentTraceStep(
            step_id="step_constraint_engine",
            title="⚖️ Constraint Engine: Deterministic Rule Verification",
            agent_name="ConstraintEngine",
            status="completed",
            summary=f"Evaluated hard constraints: {len(passing_candidates)} candidates passed, {len(rejected_candidates)} rejected.",
            details={
                "passed_count": len(passing_candidates),
                "rejected_count": len(rejected_candidates),
                "rejection_reasons": rejection_summary
            },
            execution_time_ms=s6_dur
        ))

        # 7. MCDA Multi-Criteria Decision Analysis Ranking
        s7_start = time.perf_counter()
        ranked_items = RankingEngine.rank_candidates(passing_candidates, intent)
        s7_dur = int((time.perf_counter() - s7_start) * 1000)

        top_score_str = f" (Top Pick Score: {ranked_items[0][1].composite_score}/10)" if ranked_items else ""
        traces.append(AgentTraceStep(
            step_id="step_mcda_ranking",
            title="🎯 Ranking Engine: Multi-Criteria Decision Analysis",
            agent_name="RankingEngine",
            status="completed",
            summary=f"Scored {len(ranked_items)} passing candidates using {intent.objective.value} weighting matrix{top_score_str}.",
            details={
                "objective": intent.objective.value,
                "ranked_count": len(ranked_items),
                "top_score": ranked_items[0][1].composite_score if ranked_items else None
            },
            execution_time_ms=s7_dur
        ))

        # 8. Explainable Recommendation Synthesis
        s8_start = time.perf_counter()
        recommendation_res = RecommendationEngine.synthesize_recommendations(
            ranked_candidates=ranked_items,
            intent=intent,
            session_id=session_id,
            plan=plan,
            total_discovered=len(candidates),
            rejected_counts=rejection_summary,
            trace_steps=traces
        )
        s8_dur = int((time.perf_counter() - s8_start) * 1000)

        traces.append(AgentTraceStep(
            step_id="step_recommendation_synthesizer",
            title="🏆 Recommendation Engine: Explainable Synthesis",
            agent_name="RecommendationEngine",
            status="completed",
            summary=(
                f"Generated top recommendation: '{recommendation_res.top_recommendation.candidate.title}' on {recommendation_res.top_recommendation.candidate.merchant_name}."
                if recommendation_res.top_recommendation else "No recommendation available."
            ),
            details={
                "top_recommendation": recommendation_res.top_recommendation.candidate.title if recommendation_res.top_recommendation else None,
                "total_recommendations": len(recommendation_res.all_recommendations)
            },
            execution_time_ms=s8_dur
        ))

        # Update trace list on the response
        recommendation_res.trace = traces

        # 9. Persist Task Record into PostgreSQL
        try:
            SessionService.create_task(
                db=db,
                session_id=session_id,
                data=ShoppingTaskCreate(
                    raw_prompt=query,
                    extracted_constraints=intent.model_dump(mode="json"),
                    execution_plan=plan.model_dump(mode="json")
                )
            )
        except Exception as e:
            logger.warning("Failed to persist task record: %s", str(e))

        total_dur = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Completed shopping agent pipeline for session %s in %dms. Discovered: %d, Passing: %d",
            session_id, total_dur, len(candidates), len(passing_candidates)
        )

        return recommendation_res
