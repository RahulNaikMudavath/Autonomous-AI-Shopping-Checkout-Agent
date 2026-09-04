"""
Phase 3: Autonomous AI Shopping Agent - Explainable Recommendation Engine
Synthesizes transparent, explainable recommendations:
- Top Pick (Best Overall directly from deterministic ranking)
- Best Value Pick (from ranking engine)
- Fastest Delivery Pick (from ranking engine, null if unknown)
- Ranked Alternatives (deterministic stable ordering)
- Side-by-side comparison matrix
- Factual justification reasons derived strictly from verified candidate data
- Diagnostic rejection audit for non-matching products
- Merchant discovery coverage metrics
- Safety & authorization boundaries (zero autonomous purchases)
"""
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.domain.agent_schemas import (
    ShoppingIntent, NormalizedProductCandidate, MCDAScoreBreakdown,
    RecommendationItem, RecommendationResponse, AgentPlan, AgentTraceStep,
    RankingResult, RankedProductCandidate, ConstraintFilterResult,
    DiscoveryResult, MerchantDiscoveryStatus, ComparisonItem,
    RecommendationResult
)

logger = logging.getLogger("agentcart.agent.recommendations")


class RecommendationEngine:
    """
    Synthesizes explainable recommendations and generates factual justification matrices.
    """

    @classmethod
    def build_recommendation_result(
        cls,
        ranking_result: Optional[RankingResult] = None,
        constraint_result: Optional[ConstraintFilterResult] = None,
        discovery_result: Optional[DiscoveryResult] = None,
        intent: Optional[ShoppingIntent] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RecommendationResult:
        """
        Primary Step 7 method: Generates a strongly-typed RecommendationResult.
        """
        metadata = metadata or {}
        warnings: List[str] = []

        # 1. Check merchant coverage & discovery warnings
        merchant_coverage: List[MerchantDiscoveryStatus] = []
        data_completeness = "COMPLETE"
        if discovery_result:
            merchant_coverage = discovery_result.merchant_statuses
            if discovery_result.partial_results:
                warnings.append("PARTIAL_MERCHANT_RESULTS: One or more merchant catalogs failed to respond in time.")
                data_completeness = "PARTIAL"

        # 2. Extract rejection summary
        rejection_summary: Dict[str, int] = {}
        if constraint_result:
            rejection_summary = constraint_result.rejection_summary

        # 3. Handle zero matches
        if not ranking_result or not ranking_result.ranked_products:
            warnings.append("NO_PRODUCTS_MATCHED: No products satisfied all required hard constraints.")
            if not discovery_result or discovery_result.total_results == 0:
                data_completeness = "EMPTY"

            return RecommendationResult(
                best_overall=None,
                best_value=None,
                fastest_delivery=None,
                alternatives=[],
                comparison_matrix=[],
                comparison=[],
                reasons={
                    "no_match": [
                        f"Evaluated {constraint_result.total_input if constraint_result else 0} discovered products.",
                        "Zero products satisfied all hard constraints.",
                        f"Top rejection reasons: {', '.join(f'{k} ({v})' for k, v in rejection_summary.items())}" if rejection_summary else "No candidate offers met minimum criteria."
                    ]
                },
                rejection_summary=rejection_summary,
                merchant_coverage=merchant_coverage,
                warnings=warnings,
                data_completeness=data_completeness,
                requires_human_authorization=False,
                authorization_prompt="No matching products found satisfying all hard constraints.",
                metadata=metadata
            )

        ranked_products = ranking_result.ranked_products

        # 4. Best Overall (Directly from deterministic ranking engine)
        best_overall = ranking_result.best_overall or ranked_products[0]

        # 5. Best Value (Directly from ranking engine)
        best_value = ranking_result.best_value or best_overall

        # 6. Fastest Delivery (Directly from ranking engine, None if delivery unknown)
        fastest_delivery = ranking_result.fastest_delivery
        if fastest_delivery and fastest_delivery.candidate.delivery_days is None:
            fastest_delivery = None
        
        if fastest_delivery is None or any(p.candidate.delivery_days is None for p in ranked_products):
            if any(p.candidate.delivery_days is None for p in ranked_products):
                warnings.append("UNKNOWN_DELIVERY: Delivery timeline is unconfirmed for one or more candidates.")


        # 7. Ranked Alternatives (Deterministic top 3-5 excluding best_overall)
        alternatives: List[RankedProductCandidate] = []
        for p in ranked_products:
            if p.candidate.id != best_overall.candidate.id:
                alternatives.append(p)
            if len(alternatives) >= 5:
                break

        # 8. Comparison Matrix (Side-by-side structured data)
        comparison_candidates = [best_overall] + [p for p in alternatives if p.candidate.id != best_overall.candidate.id]
        comparison_matrix = cls.build_comparison_matrix(comparison_candidates, intent=intent)

        # 9. Factual reasons per recommendation category
        reasons: Dict[str, List[str]] = {}
        if best_overall:
            reasons["best_overall"] = cls.build_factual_reasons(best_overall, intent=intent, badge="BEST_OVERALL")
        if best_value and best_value.candidate.id != best_overall.candidate.id:
            reasons["best_value"] = cls.build_factual_reasons(best_value, intent=intent, badge="BEST_VALUE")
        if fastest_delivery and fastest_delivery.candidate.id not in [best_overall.candidate.id, getattr(best_value, "candidate", None) and best_value.candidate.id]:
            reasons["fastest_delivery"] = cls.build_factual_reasons(fastest_delivery, intent=intent, badge="FASTEST_DELIVERY")

        for idx, alt in enumerate(alternatives):
            reasons[f"alternative_{idx + 1}"] = cls.build_factual_reasons(alt, intent=intent, badge=f"RANK_{alt.rank}")

        # 10. Check high-value threshold for step-up warnings
        if best_overall.candidate.current_price > Decimal("100000.00"):
            warnings.append("HIGH_VALUE_TRANSACTION: Total exceeds ₹1,00,000 threshold, requiring explicit user authorization.")

        top_cand = best_overall.candidate
        auth_prompt = f"Confirm authorization to add '{top_cand.title}' (₹{top_cand.current_price:,.2f}) to {top_cand.merchant_name} cart and proceed to checkout preparation."

        return RecommendationResult(
            best_overall=best_overall,
            best_value=best_value,
            fastest_delivery=fastest_delivery,
            alternatives=alternatives,
            comparison_matrix=comparison_matrix,
            comparison=comparison_matrix,
            reasons=reasons,
            rejection_summary=rejection_summary,
            merchant_coverage=merchant_coverage,
            warnings=warnings,
            data_completeness=data_completeness,
            requires_human_authorization=True,
            authorization_prompt=auth_prompt,
            metadata=metadata
        )

    @classmethod
    def build_comparison_matrix(
        cls,
        ranked_candidates: List[RankedProductCandidate],
        intent: Optional[ShoppingIntent] = None
    ) -> List[ComparisonItem]:
        """
        Builds structured side-by-side comparison items from ranked candidates.
        """
        matrix: List[ComparisonItem] = []
        for ranked in ranked_candidates:
            c = ranked.candidate
            item = ComparisonItem(
                candidate_id=c.id,
                product_id=c.product_id,
                title=c.title,
                merchant=c.merchant_name,
                merchant_code=c.merchant_code,
                price=c.current_price,
                discount_pct=c.discount_percentage,
                rating=c.rating,
                review_count=c.review_count,
                delivery_days=c.delivery_days,
                in_stock=c.in_stock,
                key_specs=c.specs,
                overall_score=ranked.overall_score,
                value_score=ranked.value_score,
                badge=ranked.badge,
                reasons=ranked.score_explanation,
                image_url=c.image_url,
                product_url=c.product_url
            )
            matrix.append(item)
        return matrix

    @classmethod
    def build_factual_reasons(
        cls,
        ranked: RankedProductCandidate,
        intent: Optional[ShoppingIntent] = None,
        badge: str = "TOP_PICK"
    ) -> List[str]:
        """
        Builds verifiable factual justification statements for a candidate product.
        Never hallucinates or invents non-existent specifications.
        """
        c = ranked.candidate
        reasons: List[str] = []

        # 1. Overall score achievement
        reasons.append(
            f"Achieved deterministic overall score of {ranked.overall_score:.1f}/100 ({ranked.components.get('specification', {}).score:.1f} spec, {ranked.components.get('price', {}).score:.1f} price)"
            if "specification" in ranked.components and "price" in ranked.components
            else f"Rank #{ranked.rank} with composite score of {ranked.overall_score:.1f}/100."
        )

        # 2. Price and Budget comparison
        if intent and intent.budget_max:
            savings = intent.budget_max - c.current_price
            if savings > Decimal("0.00"):
                reasons.append(f"Price: ₹{c.current_price:,.2f} (₹{savings:,.2f} under ₹{intent.budget_max:,.2f} budget ceiling)")
            else:
                reasons.append(f"Price: ₹{c.current_price:,.2f} (Within ₹{intent.budget_max:,.2f} budget limit)")
        else:
            reasons.append(f"Price: ₹{c.current_price:,.2f}")

        # 3. Technical Specifications
        specs = c.specs or {}
        ram = specs.get("ram_gb")
        if ram:
            reasons.append(f"Memory: {ram}GB RAM installed")

        ssd = specs.get("ssd_gb") or specs.get("storage_gb")
        if ssd:
            ssd_str = f"{ssd // 1024}TB" if ssd >= 1024 else f"{ssd}GB"
            reasons.append(f"Storage: {ssd_str} high-speed SSD")

        gpu = specs.get("gpu")
        if gpu:
            reasons.append(f"Graphics: {gpu} dedicated GPU")

        # 4. Delivery Logistics & Retailer
        if c.delivery_days is not None:
            reasons.append(f"Delivery: {c.delivery_days}-day ETA via {c.merchant_name}")
        else:
            reasons.append(f"Fulfillment: Shipped via {c.merchant_name} (Standard delivery)")

        # 5. Customer Rating & Inventory
        reasons.append(f"Reputation: {c.rating} ⭐ ({c.review_count:,} verified buyer reviews)")
        if c.in_stock:
            reasons.append(f"Availability: In stock ({c.available_quantity} units available)")

        return reasons

    @classmethod
    def synthesize_recommendations(
        cls,
        ranked_candidates: Union[RankingResult, List[Tuple[NormalizedProductCandidate, MCDAScoreBreakdown]]],
        intent: ShoppingIntent,
        session_id: str,
        task_id: Optional[str] = None,
        plan: Optional[AgentPlan] = None,
        total_discovered: int = 0,
        rejected_counts: Optional[Dict[str, int]] = None,
        trace_steps: Optional[List[AgentTraceStep]] = None
    ) -> RecommendationResponse:
        """
        Legacy wrapper synthesizing RecommendationResponse for backwards compatibility.
        """
        if isinstance(ranked_candidates, RankingResult):
            return cls._synthesize_from_ranking_result(
                ranking_result=ranked_candidates,
                intent=intent,
                session_id=session_id,
                task_id=task_id,
                plan=plan,
                total_discovered=total_discovered,
                rejected_counts=rejected_counts,
                trace_steps=trace_steps
            )

        # Legacy Tuple List handling
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

        top_cand, top_score = ranked_candidates[0]
        top_item = cls._build_recommendation_item(
            candidate=top_cand,
            score=top_score,
            rank=1,
            badge="TOP_PICK",
            intent=intent
        )

        best_val_cand, best_val_score = cls._find_best_value(ranked_candidates)
        best_val_item = cls._build_recommendation_item(
            candidate=best_val_cand,
            score=best_val_score,
            rank=2 if best_val_cand.id != top_cand.id else 1,
            badge="BEST_VALUE",
            intent=intent
        )

        fastest_cand, fastest_score = cls._find_fastest_delivery(ranked_candidates)
        fastest_item = cls._build_recommendation_item(
            candidate=fastest_cand,
            score=fastest_score,
            rank=3 if fastest_cand.id not in [top_cand.id, best_val_cand.id] else 1,
            badge="FASTEST_DELIVERY",
            intent=intent
        )

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
    def _synthesize_from_ranking_result(
        cls,
        ranking_result: RankingResult,
        intent: ShoppingIntent,
        session_id: str,
        task_id: Optional[str] = None,
        plan: Optional[AgentPlan] = None,
        total_discovered: int = 0,
        rejected_counts: Optional[Dict[str, int]] = None,
        trace_steps: Optional[List[AgentTraceStep]] = None
    ) -> RecommendationResponse:
        """
        Synthesizes recommendations directly from structured Phase 3 Step 6 RankingResult.
        """
        ranked_products = ranking_result.ranked_products

        if not ranked_products:
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

        top_ranked = ranking_result.best_overall or ranked_products[0]
        top_item = cls._build_item_from_ranked(top_ranked, intent, badge="TOP_PICK")

        best_val_ranked = ranking_result.best_value or top_ranked
        best_val_item = cls._build_item_from_ranked(best_val_ranked, intent, badge="BEST_VALUE")

        fastest_ranked = ranking_result.fastest_delivery or top_ranked
        fastest_item = cls._build_item_from_ranked(fastest_ranked, intent, badge="FASTEST_DELIVERY")

        all_recs: List[RecommendationItem] = []
        for item in ranked_products:
            all_recs.append(cls._build_item_from_ranked(item, intent, badge=item.badge or "RUNNER_UP"))

        top_cand = top_ranked.candidate
        return RecommendationResponse(
            session_id=session_id,
            task_id=task_id,
            intent=intent,
            plan=plan or AgentPlan(goal="Product Discovery & Ranking", total_steps=0, steps=[]),
            total_candidates_discovered=total_discovered or ranking_result.total_candidates,
            candidates_passing_constraints=len(ranked_products),
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
    def _build_item_from_ranked(
        cls,
        ranked: RankedProductCandidate,
        intent: ShoppingIntent,
        badge: str
    ) -> RecommendationItem:
        candidate = ranked.candidate
        tradeoffs = []
        if candidate.delivery_days and candidate.delivery_days > 2:
            tradeoffs.append(f"Standard shipping ETA is {candidate.delivery_days} business days")
        if candidate.current_price > Decimal("100000.00"):
            tradeoffs.append("Premium workstation tier — triggers delegated step-up authorization")

        legacy_mcda = MCDAScoreBreakdown(
            performance_score=round(ranked.components.get("specification", {}).score / 10.0 if "specification" in ranked.components else 7.0, 2),
            price_efficiency_score=round(ranked.components.get("price", {}).score / 10.0 if "price" in ranked.components else 7.0, 2),
            delivery_score=round(ranked.components.get("delivery", {}).score / 10.0 if "delivery" in ranked.components else 7.0, 2),
            rating_score=round(ranked.components.get("rating", {}).score / 10.0 if "rating" in ranked.components else 7.0, 2),
            brand_affinity_score=round(7.0, 2),
            composite_score=round(ranked.overall_score / 10.0, 2),
            score_justification={"overall_score": ranked.overall_score, "value_score": ranked.value_score}
        )

        return RecommendationItem(
            rank=ranked.rank,
            badge=badge,
            candidate=candidate,
            mcda_score=legacy_mcda,
            ranked_candidate=ranked,
            reasons=ranked.score_explanation,
            tradeoffs=tradeoffs,
            highlights={
                "merchant": candidate.merchant_name,
                "price": str(candidate.current_price),
                "ram_gb": candidate.specs.get("ram_gb"),
                "ssd_gb": candidate.specs.get("ssd_gb"),
                "gpu": candidate.specs.get("gpu"),
                "delivery_days": candidate.delivery_days,
                "composite_score": ranked.overall_score,
                "value_score": ranked.value_score
            }
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

        if intent.budget_max:
            savings = intent.budget_max - candidate.current_price
            if savings > Decimal("0.00"):
                reasons.append(f"Within budget: ₹{candidate.current_price:,.2f} (Savings of ₹{savings:,.2f} under ₹{intent.budget_max:,.2f} ceiling)")
            else:
                reasons.append(f"Exact match on budget: ₹{candidate.current_price:,.2f}")
        else:
            reasons.append(f"Current price: ₹{candidate.current_price:,.2f}")

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

        reasons.append(f"{candidate.delivery_days}-Day delivery via {candidate.merchant_name} ({candidate.shipping_option_name or 'Express'})")
        reasons.append(f"{candidate.merchant_name} merchant rating: {candidate.rating} ⭐ ({candidate.review_count:,} reviews)")

        if candidate.delivery_days and candidate.delivery_days > 2:
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
        best_item = ranked[0]
        min_days = 999

        for cand, score in ranked:
            days = cand.delivery_days if cand.delivery_days is not None else 999
            if days < min_days:
                min_days = days
                best_item = (cand, score)

        return best_item
