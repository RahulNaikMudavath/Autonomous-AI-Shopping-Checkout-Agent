"""
Phase 3: Autonomous AI Shopping Agent - Multi-Criteria Decision Analysis (MCDA) Ranking Engine
Computes calibrated multi-criteria scores across hardware performance, price efficiency, delivery speed, merchant rating, and brand affinity.
Deterministic and explainable: Outputs exact weight calculations and score breakdowns.
"""
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.domain.agent_schemas import (
    ShoppingIntent, NormalizedProductCandidate, MCDAScoreBreakdown, ObjectiveType
)

logger = logging.getLogger("agentcart.agent.ranking")


class RankingEngine:
    """
    Deterministic MCDA ranking and Pareto scoring engine.
    """

    @classmethod
    def rank_candidates(
        cls,
        candidates: List[NormalizedProductCandidate],
        intent: ShoppingIntent
    ) -> List[Tuple[NormalizedProductCandidate, MCDAScoreBreakdown]]:
        """
        Calculates MCDA scores for all candidates and sorts descending by composite score.
        """
        if not candidates:
            return []

        scored: List[Tuple[NormalizedProductCandidate, MCDAScoreBreakdown]] = []

        for candidate in candidates:
            breakdown = cls.compute_mcda_score(candidate, intent)
            scored.append((candidate, breakdown))

        # Sort descending by composite score
        scored.sort(key=lambda item: item[1].composite_score, reverse=True)
        return scored

    @classmethod
    def compute_mcda_score(
        cls,
        candidate: NormalizedProductCandidate,
        intent: ShoppingIntent
    ) -> MCDAScoreBreakdown:
        """
        Calculates individual dimension scores (0.00 - 10.00) and weighted composite score.
        """
        # 1. Performance Score (0 - 10)
        perf_score = cls._score_performance(candidate.specs, candidate.category)

        # 2. Price Efficiency Score (0 - 10)
        price_score = cls._score_price_efficiency(candidate.current_price, candidate.base_price, intent.budget_max)

        # 3. Delivery Speed Score (0 - 10)
        delivery_score = cls._score_delivery(candidate.delivery_days)

        # 4. Merchant Trust & Rating Score (0 - 10)
        rating_score = cls._score_rating(candidate.rating, candidate.review_count)

        # 5. Brand & Feature Affinity Score (0 - 10)
        affinity_score = cls._score_affinity(candidate, intent)

        # 6. Weight Vector Selection based on Objective
        weights = cls._get_objective_weights(intent.objective)

        composite = (
            (perf_score * weights["perf"]) +
            (price_score * weights["price"]) +
            (delivery_score * weights["delivery"]) +
            (rating_score * weights["rating"]) +
            (affinity_score * weights["affinity"])
        )

        composite_rounded = round(min(10.0, max(0.0, composite)), 2)

        justification = {
            "objective": intent.objective.value,
            "weights": weights,
            "dimension_scores": {
                "performance": perf_score,
                "price_efficiency": price_score,
                "delivery_speed": delivery_score,
                "merchant_rating": rating_score,
                "brand_affinity": affinity_score
            }
        }

        return MCDAScoreBreakdown(
            performance_score=round(perf_score, 2),
            price_efficiency_score=round(price_score, 2),
            delivery_score=round(delivery_score, 2),
            rating_score=round(rating_score, 2),
            brand_affinity_score=round(affinity_score, 2),
            composite_score=composite_rounded,
            score_justification=justification
        )

    @classmethod
    def _score_performance(cls, specs: Dict[str, Any], category: str) -> float:
        """
        Evaluates technical performance index (0.0 - 10.0).
        """
        score = 6.0

        # GPU / Chip Tier
        gpu_str = str(specs.get("gpu", "")).upper()
        chip_str = str(specs.get("chip", "")).upper()

        if "4090" in gpu_str:
            score += 3.5
        elif "4080" in gpu_str:
            score += 3.0
        elif "4070" in gpu_str:
            score += 2.5
        elif "4060" in gpu_str:
            score += 1.8
        elif "4050" in gpu_str:
            score += 1.0
        elif "M3 MAX" in chip_str or "M3 MAX" in gpu_str:
            score += 3.3
        elif "M3 PRO" in chip_str or "M3 PRO" in gpu_str or "M4" in chip_str:
            score += 2.4

        # RAM Capacity
        ram_gb = int(specs.get("ram_gb", 16))
        if ram_gb >= 64:
            score += 1.0
        elif ram_gb >= 32 or ram_gb == 36:
            score += 0.7
        elif ram_gb >= 24:
            score += 0.4

        # SSD Capacity
        ssd_gb = int(specs.get("ssd_gb", 512))
        if ssd_gb >= 2048:
            score += 0.5
        elif ssd_gb >= 1024:
            score += 0.3

        return min(10.0, max(2.0, score))

    @classmethod
    def _score_price_efficiency(
        cls,
        current_price: Decimal,
        base_price: Decimal,
        budget_max: Optional[Decimal]
    ) -> float:
        """
        Evaluates value for money and budget headroom (0.0 - 10.0).
        """
        score = 6.0

        # 1. Discount ratio
        if base_price > current_price and base_price > Decimal("0.00"):
            disc_pct = float((base_price - current_price) / base_price) * 100.0
            score += min(2.5, disc_pct * 0.12)

        # 2. Budget Headroom (savings relative to user's max budget)
        if budget_max and budget_max > Decimal("0.00"):
            c_p = float(current_price)
            b_m = float(budget_max)
            if c_p <= b_m:
                headroom_ratio = (b_m - c_p) / b_m
                score += min(2.0, headroom_ratio * 4.0)

        return min(10.0, max(1.0, score))

    @classmethod
    def _score_delivery(cls, delivery_days: int) -> float:
        """
        Delivery speed score: 1 day = 10.0, 2 days = 8.5, 3 days = 7.0, 4+ days = 5.0.
        """
        if delivery_days <= 1:
            return 10.0
        elif delivery_days == 2:
            return 8.5
        elif delivery_days == 3:
            return 7.0
        elif delivery_days == 4:
            return 5.5
        return 4.0

    @classmethod
    def _score_rating(cls, rating: float, review_count: int) -> float:
        """
        Normalizes rating (1-5 scale) to (0-10 scale) with confidence bonus for high review counts.
        """
        base_score = (rating / 5.0) * 9.0
        if review_count >= 500:
            base_score += 1.0
        elif review_count >= 100:
            base_score += 0.5
        return min(10.0, max(1.0, base_score))

    @classmethod
    def _score_affinity(
        cls,
        candidate: NormalizedProductCandidate,
        intent: ShoppingIntent
    ) -> float:
        """
        Evaluates brand preferences and merchant affinities.
        """
        score = 7.0

        # Brand match
        if intent.brand_preferences and candidate.brand.upper() in [b.upper() for b in intent.brand_preferences]:
            score += 2.0

        # Merchant match
        if intent.merchant_preferences and candidate.merchant_code in intent.merchant_preferences:
            score += 1.0

        return min(10.0, max(1.0, score))

    @classmethod
    def _get_objective_weights(cls, objective: ObjectiveType) -> Dict[str, float]:
        """
        Returns normalized weight vectors based on objective.
        """
        if objective == ObjectiveType.MAX_PERFORMANCE:
            return {"perf": 0.65, "price": 0.15, "delivery": 0.05, "rating": 0.10, "affinity": 0.05}
        elif objective == ObjectiveType.LOWEST_PRICE:
            return {"perf": 0.20, "price": 0.60, "delivery": 0.05, "rating": 0.10, "affinity": 0.05}
        elif objective == ObjectiveType.FASTEST_DELIVERY:
            return {"perf": 0.25, "price": 0.20, "delivery": 0.45, "rating": 0.05, "affinity": 0.05}
        elif objective == ObjectiveType.HIGHEST_RATED:
            return {"perf": 0.30, "price": 0.15, "delivery": 0.10, "rating": 0.40, "affinity": 0.05}
        elif objective == ObjectiveType.BALANCED:
            return {"perf": 0.35, "price": 0.30, "delivery": 0.15, "rating": 0.15, "affinity": 0.05}
        # Default: BEST_VALUE
        return {"perf": 0.45, "price": 0.30, "delivery": 0.10, "rating": 0.10, "affinity": 0.05}
