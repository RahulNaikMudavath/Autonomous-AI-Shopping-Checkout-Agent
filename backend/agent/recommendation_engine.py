"""
Phase 3: Autonomous AI Shopping Agent - Recommendation Synthesizer
Generates transparent, explainable recommendations:
- Top Pick (Best Overall)
- Best Value Pick
- Fastest Delivery Pick
- Runner-Up Picks
Each recommendation contains verifiable bullet points grounded in authoritative product data.
"""
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.domain.agent_schemas import (
    ShoppingIntent, NormalizedProductCandidate, MCDAScoreBreakdown,
    RecommendationItem, RecommendationResponse, AgentPlan, AgentTraceStep
)

logger = logging.getLogger("agentcart.agent.recommendations")


class RecommendationEngine:
    """
    Synthesizes explainable recommendations and generates factual justification matrices.
    """

    @classmethod
    def synthesize_recommendations(
        cls,
        ranked_candidates: List[Tuple[NormalizedProductCandidate, MCDAScoreBreakdown]],
        intent: ShoppingIntent,
        session_id: str,
        task_id: Optional[str] = None,
        plan: Optional[AgentPlan] = None,
        total_discovered: int = 0,
        rejected_counts: Optional[Dict[str, int]] = None,
        trace_steps: Optional[List[AgentTraceStep]] = None
    ) -> RecommendationResponse:
        """
        Synthesizes the final recommendation response with verified reasons and trade-offs.
        """
        if not ranked_candidates:
            return RecommendationResponse(
                session_id=session_id,
                task_id=task_id,
                intent=intent,
                plan=plan or AgentPlan(goal="Product Discovery & Ranking", total_steps=0, steps=[]),
                total_candidates_discovered=total_discovered,
                candidates_passing_constraints=0,
                top_recommendation=None,
                best_value_recommendation=None,
                fastest_delivery_recommendation=None,
                all_recommendations=[],
                rejected_candidates_summary=rejected_counts or {},
                trace=trace_steps or [],
                requires_human_authorization=False,
                authorization_reason="No matching products found satisfying all hard constraints."
            )

        # 1. Top Recommendation (Rank 1 by Composite MCDA Score)
        top_cand, top_score = ranked_candidates[0]
        top_item = cls._build_recommendation_item(
            candidate=top_cand,
            score=top_score,
            rank=1,
            badge="TOP_PICK",
            intent=intent
        )

        # 2. Best Value Recommendation (Lowest Price among top-tier performers)
        best_val_cand, best_val_score = cls._find_best_value(ranked_candidates)
        best_val_item = cls._build_recommendation_item(
            candidate=best_val_cand,
            score=best_val_score,
            rank=2 if best_val_cand.id != top_cand.id else 1,
            badge="BEST_VALUE",
            intent=intent
        )

        # 3. Fastest Delivery Recommendation
        fastest_cand, fastest_score = cls._find_fastest_delivery(ranked_candidates)
        fastest_item = cls._build_recommendation_item(
            candidate=fastest_cand,
            score=fastest_score,
            rank=3 if fastest_cand.id not in [top_cand.id, best_val_cand.id] else 1,
            badge="FASTEST_DELIVERY",
            intent=intent
        )

        # 4. Compile all recommendations list
        all_recs: List[RecommendationItem] = []
        for idx, (cand, score) in enumerate(ranked_candidates):
            badge = "TOP_PICK" if idx == 0 else ("BEST_VALUE" if cand.id == best_val_cand.id else "RUNNER_UP")
            all_recs.append(cls._build_recommendation_item(
                candidate=cand,
                score=score,
                rank=idx + 1,
                badge=badge,
                intent=intent
            ))

        return RecommendationResponse(
            session_id=session_id,
            task_id=task_id,
            intent=intent,
            plan=plan or AgentPlan(goal="Product Discovery & Ranking", total_steps=0, steps=[]),
            total_candidates_discovered=total_discovered,
            candidates_passing_constraints=len(ranked_candidates),
            top_recommendation=top_item,
            best_value_recommendation=best_val_item,
            fastest_delivery_recommendation=fastest_item,
            all_recommendations=all_recs,
            rejected_candidates_summary=rejected_counts or {},
            trace=trace_steps or [],
            requires_human_authorization=True,
            authorization_reason=f"Confirm authorization to add '{top_cand.title}' (₹{top_cand.current_price:,.2f}) to {top_cand.merchant_name} cart and proceed to checkout preparation."
        )

    @classmethod
    def _build_recommendation_item(
        cls,
        candidate: NormalizedProductCandidate,
        score: MCDAScoreBreakdown,
        rank: int,
        badge: str,
        intent: ShoppingIntent
    ) -> RecommendationItem:
        reasons = []
        tradeoffs = []

        # 1. Price reason
        if intent.budget_max:
            savings = intent.budget_max - candidate.current_price
            if savings > Decimal("0.00"):
                reasons.append(f"Within budget: ₹{candidate.current_price:,.2f} (Savings of ₹{savings:,.2f} under ₹{intent.budget_max:,.2f} ceiling)")
            else:
                reasons.append(f"Exact match on budget: ₹{candidate.current_price:,.2f}")
        else:
            reasons.append(f"Current price: ₹{candidate.current_price:,.2f}")

        # 2. Spec reasons
        ram = candidate.specs.get("ram_gb")
        if ram:
            reasons.append(f"{ram}GB high-speed memory satisfies performance requirements")

        ssd = candidate.specs.get("ssd_gb")
        if ssd:
            ssd_str = f"{ssd // 1024}TB" if ssd >= 1024 else f"{ssd}GB"
            reasons.append(f"{ssd_str} NVMe fast solid state storage")

        gpu = candidate.specs.get("gpu")
        if gpu:
            reasons.append(f"Equipped with {gpu} dedicated graphics accelerator")

        # 3. Delivery & Merchant reason
        reasons.append(f"{candidate.delivery_days}-Day delivery via {candidate.merchant_name} ({candidate.shipping_option_name or 'Express'})")
        reasons.append(f"{candidate.merchant_name} merchant rating: {candidate.rating} ⭐ ({candidate.review_count:,} reviews)")

        # 4. Trade-off considerations
        if candidate.delivery_days > 2:
            tradeoffs.append(f"Standard shipping ETA is {candidate.delivery_days} business days")
        if candidate.current_price > Decimal("100000.00"):
            tradeoffs.append("Premium workstation tier — triggers delegated step-up authorization")

        return RecommendationItem(
            rank=rank,
            badge=badge,
            candidate=candidate,
            mcda_score=score,
            reasons=reasons,
            tradeoffs=tradeoffs,
            highlights={
                "merchant": candidate.merchant_name,
                "price": str(candidate.current_price),
                "ram_gb": candidate.specs.get("ram_gb"),
                "ssd_gb": candidate.specs.get("ssd_gb"),
                "gpu": candidate.specs.get("gpu"),
                "delivery_days": candidate.delivery_days,
                "composite_score": score.composite_score
            }
        )

    @classmethod
    def _find_best_value(
        cls,
        ranked: List[Tuple[NormalizedProductCandidate, MCDAScoreBreakdown]]
    ) -> Tuple[NormalizedProductCandidate, MCDAScoreBreakdown]:
        """Finds candidate with highest value efficiency (score / price ratio)."""
        best_item = ranked[0]
        best_ratio = 0.0

        for cand, score in ranked:
            c_price = float(cand.current_price)
            if c_price > 0:
                ratio = (score.composite_score * 10000.0) / c_price
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_item = (cand, score)

        return best_item

    @classmethod
    def _find_fastest_delivery(
        cls,
        ranked: List[Tuple[NormalizedProductCandidate, MCDAScoreBreakdown]]
    ) -> Tuple[NormalizedProductCandidate, MCDAScoreBreakdown]:
        """Finds candidate with lowest delivery days, breaking ties with composite score."""
        best_item = ranked[0]
        min_days = 999

        for cand, score in ranked:
            if cand.delivery_days < min_days:
                min_days = cand.delivery_days
                best_item = (cand, score)

        return best_item
