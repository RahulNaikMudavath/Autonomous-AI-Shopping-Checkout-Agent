"""
Phase 3: Autonomous AI Shopping Agent - Constraint Engine
Evaluates hard constraints and soft preferences deterministically using pure Python & Decimal arithmetic.
Zero LLM variance: Budget limits, stock gates, and hardware minimums are non-bypassable.
"""
from decimal import Decimal
import logging
from typing import Any, List, Tuple

from backend.domain.agent_schemas import (
    ShoppingIntent, NormalizedProductCandidate, ConstraintEvaluationResult,
    SpecificationConstraint, ConstraintOperator
)
from backend.domain.marketplace import AvailabilityState
from backend.services.pricing_service import quantize_money

logger = logging.getLogger("agentcart.agent.constraints")


class ConstraintEngine:
    """
    Deterministic validation engine for non-negotiable commerce and specification constraints.
    """

    @classmethod
    def evaluate_candidate(
        cls,
        candidate: NormalizedProductCandidate,
        intent: ShoppingIntent
    ) -> ConstraintEvaluationResult:
        """
        Runs the full verification checklist on a candidate.
        Returns a structured ConstraintEvaluationResult.
        """
        passed_rules: List[str] = []
        failed_rules: List[str] = []
        soft_penalties: List[str] = []

        # 1. Hard Constraint: Maximum Budget Gate
        if intent.budget_max is not None:
            max_b = quantize_money(intent.budget_max)
            if candidate.current_price > max_b:
                failed_rules.append(
                    f"Price ₹{candidate.current_price:,.2f} exceeds maximum budget ₹{max_b:,.2f}"
                )
            else:
                passed_rules.append(
                    f"Within budget (₹{candidate.current_price:,.2f} <= ₹{max_b:,.2f})"
                )

        # 2. Hard Constraint: Minimum Budget Filter (if specified)
        if intent.budget_min is not None:
            min_b = quantize_money(intent.budget_min)
            if candidate.current_price < min_b:
                failed_rules.append(
                    f"Price ₹{candidate.current_price:,.2f} is below minimum threshold ₹{min_b:,.2f}"
                )
            else:
                passed_rules.append(f"Above minimum price filter (₹{candidate.current_price:,.2f})")

        # 3. Hard Constraint: Stock Availability Gate
        if intent.require_in_stock:
            if not candidate.in_stock or candidate.inventory_state == AvailabilityState.OUT_OF_STOCK:
                failed_rules.append("Product is out of stock across merchant warehouses")
            else:
                passed_rules.append(f"In stock (Available: {candidate.available_quantity} units)")

        # 4. Hard/Soft Constraints: Specification Rules
        for constraint in intent.spec_constraints:
            spec_key = constraint.key
            spec_val = candidate.specs.get(spec_key)

            is_satisfied, reason = cls._check_operator(spec_key, spec_val, constraint.operator, constraint.target_value)

            if is_satisfied:
                passed_rules.append(reason)
            else:
                if constraint.is_hard_constraint:
                    failed_rules.append(reason)
                else:
                    soft_penalties.append(reason)

        # 5. Hard Constraint: Required Keywords
        combined_text = f"{candidate.title} {candidate.brand} {candidate.model or ''} {' '.join(str(v) for v in candidate.specs.values())}".lower()
        for kw in intent.required_keywords:
            if kw.lower() not in combined_text:
                failed_rules.append(f"Missing required keyword: '{kw}'")
            else:
                passed_rules.append(f"Contains required keyword: '{kw}'")

        # 6. Hard Constraint: Excluded Keywords
        for kw in intent.excluded_keywords:
            if kw.lower() in combined_text:
                failed_rules.append(f"Contains excluded keyword: '{kw}'")

        # 7. Soft/Hard Constraint: Minimum Merchant Rating
        if candidate.rating < intent.min_rating:
            soft_penalties.append(f"Merchant rating {candidate.rating} is below preferred {intent.min_rating}")
        else:
            passed_rules.append(f"Merchant rating {candidate.rating} >= {intent.min_rating}")

        # 8. Soft Preference: Merchant Filter
        if intent.merchant_preferences and candidate.merchant_code not in intent.merchant_preferences:
            soft_penalties.append(f"Merchant {candidate.merchant_code} is not in user preferred merchants {intent.merchant_preferences}")

        passed_all = len(failed_rules) == 0

        return ConstraintEvaluationResult(
            candidate_id=candidate.id,
            passed_all_hard_constraints=passed_all,
            passed_constraints=passed_rules,
            failed_constraints=failed_rules,
            soft_penalties=soft_penalties
        )

    @classmethod
    def filter_candidates(
        cls,
        candidates: List[NormalizedProductCandidate],
        intent: ShoppingIntent
    ) -> Tuple[List[NormalizedProductCandidate], List[Tuple[NormalizedProductCandidate, List[str]]]]:
        """
        Partitions candidates into passing candidates and rejected candidates with reasons.
        """
        passing = []
        rejected = []

        for c in candidates:
            res = cls.evaluate_candidate(c, intent)
            if res.passed_all_hard_constraints:
                passing.append(c)
            else:
                rejected.append((c, res.failed_constraints))

        logger.info(
            "Constraint filtering completed. %d passed, %d rejected out of %d total candidates.",
            len(passing), len(rejected), len(candidates)
        )
        return passing, rejected

    @classmethod
    def _check_operator(
        cls,
        key: str,
        actual_val: Any,
        operator: ConstraintOperator,
        target_val: Any
    ) -> Tuple[bool, str]:
        """
        Safely tests binary operator comparisons.
        """
        if actual_val is None:
            return False, f"Specification '{key}' not specified by merchant"

        try:
            if operator == ConstraintOperator.GTE:
                # Numeric comparison
                act_num = float(actual_val)
                tgt_num = float(target_val)
                if act_num >= tgt_num:
                    return True, f"Specification '{key}' ({actual_val}) >= {target_val}"
                return False, f"Specification '{key}' ({actual_val}) is less than required {target_val}"

            elif operator == ConstraintOperator.LTE:
                act_num = float(actual_val)
                tgt_num = float(target_val)
                if act_num <= tgt_num:
                    return True, f"Specification '{key}' ({actual_val}) <= {target_val}"
                return False, f"Specification '{key}' ({actual_val}) exceeds limit of {target_val}"

            elif operator == ConstraintOperator.EQ:
                if str(actual_val).lower() == str(target_val).lower():
                    return True, f"Specification '{key}' equals {target_val}"
                return False, f"Specification '{key}' ({actual_val}) does not match {target_val}"

            elif operator == ConstraintOperator.CONTAINS:
                if str(target_val).lower() in str(actual_val).lower():
                    return True, f"Specification '{key}' contains '{target_val}'"
                return False, f"Specification '{key}' ({actual_val}) does not contain '{target_val}'"

            elif operator == ConstraintOperator.IN:
                if isinstance(target_val, list) and actual_val in target_val:
                    return True, f"Specification '{key}' ({actual_val}) in {target_val}"
                return False, f"Specification '{key}' ({actual_val}) not in {target_val}"

        except (ValueError, TypeError) as e:
            return False, f"Could not evaluate constraint on '{key}': {str(e)}"

        return False, f"Unknown operator {operator}"
