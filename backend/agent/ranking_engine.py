"""
Phase 3 Step 6: Autonomous AI Shopping Agent - Deterministic MCDA Ranking Engine
Computes calibrated multi-criteria scores across hardware specifications, price efficiency,
delivery speed, merchant rating, discounts, inventory health, and soft preference affinity.

100% Deterministic and explainable:
- Pure Decimal precision for monetary calculations.
- Normalized 0.0 - 100.0 component scoring.
- Bounded weight adjustments enforcing the 100% sum invariant.
- Explicit multi-level tie-breaking policy.
- Zero LLM in scoring or winner selection.
- Complete defense against prompt injection / adversarial merchant text.
"""
from decimal import Decimal
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.domain.agent_schemas import (
    ShoppingIntent, NormalizedProductCandidate, MCDAScoreBreakdown, ObjectiveType,
    ScoreComponentBreakdown, RankedProductCandidate, RankingResult
)

logger = logging.getLogger("agentcart.agent.ranking")


class RankingEngine:
    """
    Deterministic MCDA ranking and Pareto scoring engine.
    """

    DEFAULT_PROFILE = "default_v1"

    # Base profile weights (must sum to 100.0)
    BASE_WEIGHTS: Dict[str, float] = {
        "price": 30.0,
        "specification": 25.0,
        "delivery": 20.0,
        "rating": 15.0,
        "discount": 5.0,
        "inventory": 5.0
    }

    # Objective-specific weight matrices (all strictly sum to 100.0)
    OBJECTIVE_WEIGHTS: Dict[ObjectiveType, Dict[str, float]] = {
        ObjectiveType.MAX_PERFORMANCE: {
            "specification": 50.0, "price": 15.0, "delivery": 10.0, "rating": 15.0, "discount": 5.0, "inventory": 5.0
        },
        ObjectiveType.LOWEST_PRICE: {
            "price": 55.0, "specification": 15.0, "delivery": 10.0, "rating": 10.0, "discount": 5.0, "inventory": 5.0
        },
        ObjectiveType.FASTEST_DELIVERY: {
            "delivery": 45.0, "price": 20.0, "specification": 15.0, "rating": 10.0, "discount": 5.0, "inventory": 5.0
        },
        ObjectiveType.HIGHEST_RATED: {
            "rating": 45.0, "price": 20.0, "specification": 15.0, "delivery": 10.0, "discount": 5.0, "inventory": 5.0
        },
        ObjectiveType.BEST_VALUE: {
            "price": 35.0, "specification": 30.0, "delivery": 15.0, "rating": 10.0, "discount": 5.0, "inventory": 5.0
        },
        ObjectiveType.BALANCED: {
            "price": 30.0, "specification": 25.0, "delivery": 20.0, "rating": 15.0, "discount": 5.0, "inventory": 5.0
        }
    }

    TIE_BREAK_POLICY: List[str] = [
        "1. Overall Score (descending)",
        "2. Specification Score (descending)",
        "3. Merchant Rating Score (descending)",
        "4. Delivery Speed in Days (ascending)",
        "5. Current Price in INR (ascending)",
        "6. Stable Candidate ID (ascending)"
    ]

    @classmethod
    def rank_products(
        cls,
        candidates: List[NormalizedProductCandidate],
        intent: ShoppingIntent,
        scoring_profile: str = "default_v1"
    ) -> RankingResult:
        """
        Main Phase 3 Step 6 Ranking API:
        Evaluates valid product candidates against multi-criteria scoring vectors,
        resolves Best Overall, Best Value, and Fastest Delivery, and outputs transparent breakdowns.
        """
        start_time = time.perf_counter()

        # 1. Filter / Validate candidates for ranking safety
        valid_candidates = cls._validate_candidates_for_ranking(candidates)
        if not valid_candidates:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return RankingResult(
                ranked_products=[],
                best_overall=None,
                best_value=None,
                fastest_delivery=None,
                scoring_profile=scoring_profile,
                weights_applied=cls.get_weights(intent.objective),
                total_candidates=0,
                tie_break_policy=cls.TIE_BREAK_POLICY,
                execution_time_ms=elapsed_ms,
                metadata={"reason": "No valid candidates provided for ranking"}
            )

        # 2. Resolve validated weights
        weights = cls.get_weights(intent.objective)

        # 3. Calculate candidate pool price boundaries for relative price scoring
        min_price, max_price = cls._compute_price_bounds(valid_candidates)

        # 4. Score each candidate across all 6 dimensions
        scored_candidates: List[RankedProductCandidate] = []
        for candidate in valid_candidates:
            ranked_item = cls._score_candidate(
                candidate=candidate,
                intent=intent,
                weights=weights,
                min_price=min_price,
                max_price=max_price
            )
            scored_candidates.append(ranked_item)

        # 5. Deterministic sorting for Best Overall
        # Primary sort key: (-overall_score, -spec_score, -rating_score, delivery_days, price, id)
        scored_candidates.sort(
            key=lambda item: (
                -round(item.overall_score, 2),
                -round(item.components["specification"].score, 2),
                -round(item.components["rating"].score, 2),
                item.candidate.delivery_days if item.candidate.delivery_days and item.candidate.delivery_days > 0 else 999,
                item.candidate.current_price,
                item.candidate.id
            )
        )

        # Assign 1-based ranks
        for idx, item in enumerate(scored_candidates):
            item.rank = idx + 1

        # 6. Identify Special Recommendations (Best Overall, Best Value, Fastest Delivery)
        best_overall = scored_candidates[0] if scored_candidates else None
        if best_overall:
            best_overall.badge = "TOP_PICK"

        best_value = cls._select_best_value(scored_candidates)
        if best_value and best_value.candidate.id != (best_overall.candidate.id if best_overall else None):
            best_value.badge = "BEST_VALUE"

        fastest_delivery = cls._select_fastest_delivery(scored_candidates)
        if fastest_delivery and fastest_delivery.candidate.id not in [
            best_overall.candidate.id if best_overall else None,
            best_value.candidate.id if best_value else None
        ]:
            fastest_delivery.badge = "FASTEST_DELIVERY"

        # Assign RUNNER_UP badge to others
        for item in scored_candidates:
            if not item.badge:
                item.badge = "RUNNER_UP"

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return RankingResult(
            ranked_products=scored_candidates,
            best_overall=best_overall,
            best_value=best_value,
            fastest_delivery=fastest_delivery,
            scoring_profile=scoring_profile,
            weights_applied=weights,
            total_candidates=len(scored_candidates),
            tie_break_policy=cls.TIE_BREAK_POLICY,
            execution_time_ms=elapsed_ms,
            metadata={
                "objective": intent.objective.value,
                "price_range": {
                    "min": str(min_price),
                    "max": str(max_price)
                }
            }
        )

    @classmethod
    def get_weights(cls, objective: Optional[ObjectiveType] = None) -> Dict[str, float]:
        """
        Returns validated weight vector. Validates that sum equals 100.0%.
        """
        if objective and objective in cls.OBJECTIVE_WEIGHTS:
            weights = dict(cls.OBJECTIVE_WEIGHTS[objective])
        else:
            weights = dict(cls.BASE_WEIGHTS)

        # Enforce sum to 100.0
        total = sum(weights.values())
        if abs(total - 100.0) > 0.001:
            # Normalize to strictly 100.0
            weights = {k: round((v / total) * 100.0, 2) for k, v in weights.items()}
        return weights

    @classmethod
    def _validate_candidates_for_ranking(
        cls,
        candidates: List[NormalizedProductCandidate]
    ) -> List[NormalizedProductCandidate]:
        """
        Ensures candidates have valid authoritative data. Rejects corrupted or invalid items.
        """
        valid: List[NormalizedProductCandidate] = []
        for cand in candidates:
            if not cand or not cand.id:
                continue
            # Validate non-negative price
            if cand.current_price is None or cand.current_price < Decimal("0.00"):
                continue
            # Validate rating range if present
            if cand.rating is not None and (cand.rating < 0.0 or cand.rating > 5.0):
                continue
            valid.append(cand)
        return valid

    @classmethod
    def _compute_price_bounds(
        cls,
        candidates: List[NormalizedProductCandidate]
    ) -> Tuple[Decimal, Decimal]:
        """Finds minimum and maximum prices in the valid candidate pool."""
        prices = [c.current_price for c in candidates if c.current_price is not None]
        if not prices:
            return Decimal("0.00"), Decimal("0.00")
        return min(prices), max(prices)

    @classmethod
    def _score_candidate(
        cls,
        candidate: NormalizedProductCandidate,
        intent: ShoppingIntent,
        weights: Dict[str, float],
        min_price: Decimal,
        max_price: Decimal
    ) -> RankedProductCandidate:
        """
        Calculates all 6 component scores (0.0 - 100.0) and composite overall / value score.
        """
        # 1. Price Score (0 - 100)
        price_score, price_raw, price_desc = cls._score_price(
            current_price=candidate.current_price,
            min_price=min_price,
            max_price=max_price,
            budget_max=intent.budget_max
        )

        # 2. Specification Score (0 - 100)
        spec_score, spec_raw, spec_desc = cls._score_specification(
            candidate=candidate,
            intent=intent
        )

        # 3. Delivery Score (0 - 100)
        delivery_score, delivery_raw, delivery_desc = cls._score_delivery(
            delivery_days=candidate.delivery_days
        )

        # 4. Rating Score (0 - 100)
        rating_score, rating_raw, rating_desc = cls._score_rating(
            rating=candidate.rating,
            review_count=candidate.review_count
        )

        # 5. Discount Score (0 - 100)
        discount_score, discount_raw, discount_desc = cls._score_discount(
            discount_percentage=candidate.discount_percentage,
            base_price=candidate.base_price,
            current_price=candidate.current_price
        )

        # 6. Inventory Score (0 - 100)
        inventory_score, inventory_raw, inventory_desc = cls._score_inventory(
            in_stock=candidate.in_stock,
            available_quantity=candidate.available_quantity
        )

        # Build component breakdown
        components: Dict[str, ScoreComponentBreakdown] = {
            "price": ScoreComponentBreakdown(
                score=round(price_score, 2),
                weight=weights["price"],
                weighted_score=round((price_score * weights["price"]) / 100.0, 2),
                raw_value=price_raw,
                description=price_desc
            ),
            "specification": ScoreComponentBreakdown(
                score=round(spec_score, 2),
                weight=weights["specification"],
                weighted_score=round((spec_score * weights["specification"]) / 100.0, 2),
                raw_value=spec_raw,
                description=spec_desc
            ),
            "delivery": ScoreComponentBreakdown(
                score=round(delivery_score, 2),
                weight=weights["delivery"],
                weighted_score=round((delivery_score * weights["delivery"]) / 100.0, 2),
                raw_value=delivery_raw,
                description=delivery_desc
            ),
            "rating": ScoreComponentBreakdown(
                score=round(rating_score, 2),
                weight=weights["rating"],
                weighted_score=round((rating_score * weights["rating"]) / 100.0, 2),
                raw_value=rating_raw,
                description=rating_desc
            ),
            "discount": ScoreComponentBreakdown(
                score=round(discount_score, 2),
                weight=weights["discount"],
                weighted_score=round((discount_score * weights["discount"]) / 100.0, 2),
                raw_value=discount_raw,
                description=discount_desc
            ),
            "inventory": ScoreComponentBreakdown(
                score=round(inventory_score, 2),
                weight=weights["inventory"],
                weighted_score=round((inventory_score * weights["inventory"]) / 100.0, 2),
                raw_value=inventory_raw,
                description=inventory_desc
            )
        }

        # Composite overall score = sum of weighted scores (0.0 - 100.0)
        overall_score = sum(c.weighted_score for c in components.values())
        overall_score = round(min(100.0, max(0.0, overall_score)), 2)

        # Deterministic Value score = (Spec * 0.35) + (Price * 0.45) + (Rating * 0.10) + (Discount * 0.10)
        value_score = (
            (spec_score * 0.35) +
            (price_score * 0.45) +
            (rating_score * 0.10) +
            (discount_score * 0.10)
        )
        value_score = round(min(100.0, max(0.0, value_score)), 2)

        # Generate verifiable factual bullet points
        explanations = cls._generate_score_explanations(
            candidate=candidate,
            intent=intent,
            components=components,
            overall_score=overall_score
        )

        return RankedProductCandidate(
            candidate=candidate,
            rank=1,
            overall_score=overall_score,
            value_score=value_score,
            components=components,
            score_explanation=explanations,
            badge=None
        )

    # -------------------------------------------------------------------------
    # Deterministic Dimension Scoring Methods
    # -------------------------------------------------------------------------

    @classmethod
    def _score_price(
        cls,
        current_price: Decimal,
        min_price: Decimal,
        max_price: Decimal,
        budget_max: Optional[Decimal]
    ) -> Tuple[float, str, str]:
        """
        Scores price efficiency on a 0.0 - 100.0 scale.
        Cheapest candidate in the pool receives 100.0; highest price scales to 50.0.
        If all prices equal, budget headroom determines score.
        """
        raw_str = f"₹{current_price:,.2f}"

        if current_price < Decimal("0.00"):
            return 0.0, raw_str, "Invalid negative price"

        if max_price > min_price:
            ratio = float((max_price - current_price) / (max_price - min_price))
            score = 50.0 + (ratio * 50.0)
            desc = f"Relative price position: {ratio*100:.1f}% savings against max candidate price"
        else:
            if budget_max and budget_max > Decimal("0.00") and current_price <= budget_max:
                headroom_ratio = float((budget_max - current_price) / budget_max)
                score = min(100.0, 80.0 + (headroom_ratio * 20.0))
                desc = f"Exact or below budget ceiling with {headroom_ratio*100:.1f}% headroom"
            else:
                score = 100.0
                desc = "Uniform candidate price"

        return round(min(100.0, max(0.0, score)), 2), raw_str, desc

    @classmethod
    def _score_specification(
        cls,
        candidate: NormalizedProductCandidate,
        intent: ShoppingIntent
    ) -> Tuple[float, str, str]:
        """
        Scores technical hardware and feature capabilities deterministically (0.0 - 100.0).
        Base score is 60.0 for passing minimum hard constraints. Extra tiers yield bonuses.
        """
        score = 60.0
        specs = candidate.specs or {}
        reasons = []

        # 1. GPU / Chip Tier
        gpu_str = str(specs.get("gpu", "")).upper()
        chip_str = str(specs.get("chip", "")).upper()

        if "4090" in gpu_str:
            score += 20.0
            reasons.append("RTX 4090 Flagship")
        elif "4080" in gpu_str:
            score += 16.0
            reasons.append("RTX 4080 High-End")
        elif "4070" in gpu_str:
            score += 12.0
            reasons.append("RTX 4070 Performance")
        elif "4060" in gpu_str:
            score += 8.0
            reasons.append("RTX 4060 Mainstream")
        elif "4050" in gpu_str or "3060" in gpu_str or "3050" in gpu_str:
            score += 4.0
            reasons.append("RTX Entry Dedicated GPU")
        elif "M3 MAX" in chip_str or "M3 MAX" in gpu_str or "M4 MAX" in chip_str:
            score += 19.0
            reasons.append("Apple Silicon Max Tier")
        elif "M3 PRO" in chip_str or "M3 PRO" in gpu_str or "M4 PRO" in chip_str or "M4" in chip_str:
            score += 12.0
            reasons.append("Apple Silicon Pro Tier")

        # 2. RAM Capacity
        ram_gb = int(specs.get("ram_gb", 16) or 16)
        if ram_gb >= 64:
            score += 10.0
            reasons.append(f"{ram_gb}GB RAM (Heavy Workstation)")
        elif ram_gb >= 32 or ram_gb == 36:
            score += 6.0
            reasons.append(f"{ram_gb}GB RAM (Pro Multitasking)")
        elif ram_gb >= 24:
            score += 3.0
            reasons.append(f"{ram_gb}GB RAM")

        # 3. SSD Capacity
        ssd_gb = int(specs.get("ssd_gb", 512) or 512)
        if ssd_gb >= 2048:
            score += 6.0
            reasons.append(f"{ssd_gb // 1024}TB NVMe Storage")
        elif ssd_gb >= 1024:
            score += 4.0
            reasons.append("1TB NVMe Storage")

        # 4. Soft Brand Preference Affinity Bonus (Bounded: +5.0)
        if intent.brand_preferences and candidate.brand:
            if candidate.brand.upper() in [b.upper() for b in intent.brand_preferences]:
                score += 5.0
                reasons.append(f"Preferred Brand: {candidate.brand}")

        # 5. Soft Merchant Preference Affinity Bonus (Bounded: +5.0)
        if intent.merchant_preferences and candidate.merchant_code:
            if candidate.merchant_code.upper() in [m.upper() for m in intent.merchant_preferences]:
                score += 5.0
                reasons.append(f"Preferred Merchant: {candidate.merchant_code}")

        raw_str = f"{ram_gb}GB RAM | {ssd_gb}GB SSD | {gpu_str or chip_str or 'Integrated'}"
        desc = "; ".join(reasons) if reasons else "Standard specification match"
        return min(100.0, max(0.0, score)), raw_str, desc

    @classmethod
    def _score_delivery(cls, delivery_days: Optional[int]) -> Tuple[float, str, str]:
        """
        Scores delivery speed deterministically:
        1 day = 100.0, 2 days = 70.0, 3 days = 45.0, 4 days = 25.0, 5+ days = 10.0.
        Unknown delivery = 20.0 (explicit unknown policy: unknown != best).
        """
        if delivery_days is None or delivery_days <= 0:
            return 20.0, "Unknown", "Unknown delivery time (neutral fallback penalty)"

        raw_str = f"{delivery_days} day{'s' if delivery_days != 1 else ''}"
        if delivery_days == 1:
            return 100.0, raw_str, "Next-Day Priority Delivery"
        elif delivery_days == 2:
            return 70.0, raw_str, "2-Day Express Delivery"
        elif delivery_days == 3:
            return 45.0, raw_str, "3-Day Standard Delivery"
        elif delivery_days == 4:
            return 25.0, raw_str, "4-Day Ground Shipping"
        else:
            return 10.0, raw_str, f"{delivery_days}-Day Extended Logistics"

    @classmethod
    def _score_rating(
        cls,
        rating: Optional[float],
        review_count: Optional[int]
    ) -> Tuple[float, str, str]:
        """
        Scores authoritative merchant rating (0.0 - 5.0 scale normalized to 0 - 90),
        plus a review-count confidence bonus (up to +10.0 points).
        Unknown rating = 60.0 (neutral policy).
        """
        if rating is None:
            return 60.0, "Unrated", "No authoritative merchant rating available"

        if rating < 0.0 or rating > 5.0:
            return 0.0, f"{rating} ⭐", "Invalid rating bounds"

        # Base rating score (5.0 -> 90.0, 4.0 -> 72.0, 3.0 -> 54.0)
        base_score = (rating / 5.0) * 90.0

        # Review volume confidence bonus
        reviews = review_count or 0
        if reviews >= 1000:
            bonus = 10.0
        elif reviews >= 500:
            bonus = 7.0
        elif reviews >= 100:
            bonus = 4.0
        elif reviews >= 10:
            bonus = 2.0
        else:
            bonus = 0.0

        final_score = min(100.0, base_score + bonus)
        raw_str = f"{rating:.1f} ⭐ ({reviews:,} reviews)"
        desc = f"Rating: {rating:.1f}/5.0 with {reviews:,} verified merchant reviews"
        return round(final_score, 2), raw_str, desc

    @classmethod
    def _score_discount(
        cls,
        discount_percentage: Optional[float],
        base_price: Optional[Decimal],
        current_price: Optional[Decimal]
    ) -> Tuple[float, str, str]:
        """
        Scores authoritative merchant discount percentage (0.0 - 100.0 scale).
        10% discount -> 25.0, 20% -> 50.0, 40%+ -> 100.0.
        0% or unknown -> 10.0.
        """
        disc_pct = float(discount_percentage or 0.0)
        if disc_pct <= 0.0 and base_price and current_price and base_price > current_price and base_price > Decimal("0.00"):
            disc_pct = float((base_price - current_price) / base_price) * 100.0

        if disc_pct <= 0.0:
            return 10.0, "0%", "No promotional discount applied"

        # Bounded normalization: 40% discount reaches 100.0
        score = min(100.0, disc_pct * 2.5)
        raw_str = f"{disc_pct:.1f}% OFF"
        desc = f"Verified merchant discount of {disc_pct:.1f}%"
        return round(score, 2), raw_str, desc

    @classmethod
    def _score_inventory(
        cls,
        in_stock: bool,
        available_quantity: Optional[int]
    ) -> Tuple[float, str, str]:
        """
        Scores stock health deterministically:
        10+ units = 100.0, 3-9 units = 80.0, 1-2 units = 50.0 (LOW_STOCK), Out of Stock = 0.0.
        """
        if not in_stock:
            return 0.0, "OUT_OF_STOCK", "Item is currently out of stock"

        qty = available_quantity if available_quantity is not None else 10
        if qty >= 10:
            return 100.0, f"In Stock ({qty} available)", "Healthy inventory buffer"
        elif qty >= 3:
            return 80.0, f"In Stock ({qty} available)", "Adequate stock quantity"
        elif qty >= 1:
            return 50.0, f"Low Stock ({qty} available)", "Limited quantity remaining"
        else:
            return 0.0, "OUT_OF_STOCK", "Zero inventory available"

    # -------------------------------------------------------------------------
    # Recommendation Selection Helpers
    # -------------------------------------------------------------------------

    @classmethod
    def _select_best_value(
        cls,
        ranked: List[RankedProductCandidate]
    ) -> Optional[RankedProductCandidate]:
        """
        Selects candidate with the highest value score.
        Tie-breaker: (value_score desc, current_price asc, spec_score desc, id asc).
        """
        if not ranked:
            return None
        sorted_by_val = sorted(
            ranked,
            key=lambda item: (
                -round(item.value_score, 2),
                item.candidate.current_price,
                -round(item.components["specification"].score, 2),
                item.candidate.id
            )
        )
        return sorted_by_val[0]

    @classmethod
    def _select_fastest_delivery(
        cls,
        ranked: List[RankedProductCandidate]
    ) -> Optional[RankedProductCandidate]:
        """
        Selects candidate with shortest authoritative delivery days.
        Must have known positive delivery days (delivery_days > 0). If all unknown, returns None.
        Tie-breaker: (delivery_days asc, overall_score desc, current_price asc, id asc).
        """
        known_delivery = [
            item for item in ranked
            if item.candidate.delivery_days is not None and item.candidate.delivery_days > 0
        ]
        if not known_delivery:
            return None

        sorted_by_delivery = sorted(
            known_delivery,
            key=lambda item: (
                item.candidate.delivery_days,
                -round(item.overall_score, 2),
                item.candidate.current_price,
                item.candidate.id
            )
        )
        return sorted_by_delivery[0]

    @classmethod
    def _generate_score_explanations(
        cls,
        candidate: NormalizedProductCandidate,
        intent: ShoppingIntent,
        components: Dict[str, ScoreComponentBreakdown],
        overall_score: float
    ) -> List[str]:
        """
        Builds transparent, verifiable bullet points grounded in deterministic facts.
        """
        reasons: List[str] = []

        # 1. Price & Budget
        if intent.budget_max and intent.budget_max > Decimal("0.00"):
            savings = intent.budget_max - candidate.current_price
            if savings > Decimal("0.00"):
                reasons.append(
                    f"Within budget: ₹{candidate.current_price:,.2f} (Savings of ₹{savings:,.2f} under ₹{intent.budget_max:,.2f} budget ceiling)"
                )
            else:
                reasons.append(f"Exact match on budget: ₹{candidate.current_price:,.2f}")
        else:
            reasons.append(f"Authoritative merchant price: ₹{candidate.current_price:,.2f}")

        # 2. Specs
        specs = candidate.specs or {}
        ram = specs.get("ram_gb")
        if ram:
            reasons.append(f"{ram}GB high-speed memory satisfies performance constraints")

        ssd = specs.get("ssd_gb")
        if ssd:
            ssd_str = f"{ssd // 1024}TB" if ssd >= 1024 else f"{ssd}GB"
            reasons.append(f"{ssd_str} fast NVMe solid-state storage")

        gpu = specs.get("gpu")
        if gpu:
            reasons.append(f"Equipped with {gpu} dedicated graphics accelerator")

        # 3. Delivery
        if candidate.delivery_days and candidate.delivery_days > 0:
            reasons.append(
                f"{candidate.delivery_days}-Day delivery via {candidate.merchant_name} ({candidate.shipping_option_name or 'Standard/Express'})"
            )
        else:
            reasons.append(f"Fulfillment via {candidate.merchant_name}")

        # 4. Rating
        if candidate.rating:
            reasons.append(
                f"{candidate.merchant_name} rating: {candidate.rating} ⭐ ({candidate.review_count:,} verified reviews)"
            )

        # 5. Soft preferences
        if intent.brand_preferences and candidate.brand:
            if candidate.brand.upper() in [b.upper() for b in intent.brand_preferences]:
                reasons.append(f"Matches preferred brand: {candidate.brand}")

        if intent.merchant_preferences and candidate.merchant_code:
            if candidate.merchant_code.upper() in [m.upper() for m in intent.merchant_preferences]:
                reasons.append(f"Matches preferred merchant: {candidate.merchant_code}")

        return reasons

    # -------------------------------------------------------------------------
    # Backwards Compatibility APIs
    # -------------------------------------------------------------------------

    @classmethod
    def rank_candidates(
        cls,
        candidates: List[NormalizedProductCandidate],
        intent: ShoppingIntent
    ) -> List[Tuple[NormalizedProductCandidate, MCDAScoreBreakdown]]:
        """
        Backwards-compatible API returning List of (candidate, MCDAScoreBreakdown).
        Uses the new deterministic MCDA ranking internally.
        """
        if not candidates:
            return []

        res = cls.rank_products(candidates=candidates, intent=intent)
        result: List[Tuple[NormalizedProductCandidate, MCDAScoreBreakdown]] = []

        for item in res.ranked_products:
            # Map 0-100 scores to 0-10 scale for legacy MCDAScoreBreakdown
            breakdown = MCDAScoreBreakdown(
                performance_score=round(item.components["specification"].score / 10.0, 2),
                price_efficiency_score=round(item.components["price"].score / 10.0, 2),
                delivery_score=round(item.components["delivery"].score / 10.0, 2),
                rating_score=round(item.components["rating"].score / 10.0, 2),
                brand_affinity_score=round(
                    (item.components["specification"].score if "preferred" in (item.components["specification"].description or "").lower() else 70.0) / 10.0, 2
                ),
                composite_score=round(item.overall_score / 10.0, 2),
                score_justification={
                    "overall_score": item.overall_score,
                    "value_score": item.value_score,
                    "components": {k: v.model_dump() for k, v in item.components.items()},
                    "weights": res.weights_applied
                }
            )
            result.append((item.candidate, breakdown))

        return result

    @classmethod
    def compute_mcda_score(
        cls,
        candidate: NormalizedProductCandidate,
        intent: ShoppingIntent
    ) -> MCDAScoreBreakdown:
        """
        Backwards-compatible single-candidate MCDA scorer.
        """
        ranked_res = cls.rank_products(candidates=[candidate], intent=intent)
        if not ranked_res.ranked_products:
            return MCDAScoreBreakdown(
                performance_score=5.0,
                price_efficiency_score=5.0,
                delivery_score=5.0,
                rating_score=5.0,
                brand_affinity_score=5.0,
                composite_score=5.0,
                score_justification={}
            )
        item = ranked_res.ranked_products[0]
        return MCDAScoreBreakdown(
            performance_score=round(item.components["specification"].score / 10.0, 2),
            price_efficiency_score=round(item.components["price"].score / 10.0, 2),
            delivery_score=round(item.components["delivery"].score / 10.0, 2),
            rating_score=round(item.components["rating"].score / 10.0, 2),
            brand_affinity_score=round(7.0, 2),
            composite_score=round(item.overall_score / 10.0, 2),
            score_justification={
                "overall_score": item.overall_score,
                "value_score": item.value_score,
                "components": {k: v.model_dump() for k, v in item.components.items()}
            }
        )
