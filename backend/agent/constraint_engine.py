"""
Phase 3 Step 5: Autonomous AI Shopping Agent - Deterministic Hard-Constraint Engine
Evaluates non-negotiable commerce and specification constraints deterministically.
Zero LLM variance: Budget boundaries (exact Decimal), stock availability, RAM/Storage minimums,
GPU family requirements, and exclusions are non-bypassable and strictly reproducible.
"""
from decimal import Decimal
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.domain.agent_schemas import (
    ShoppingIntent, NormalizedProductCandidate,
    ConstraintEvaluationResult, ConstraintViolation,
    ConstraintFilterResult, SpecificationConstraint, ConstraintOperator
)
from backend.domain.marketplace import AvailabilityState
from backend.services.pricing_service import quantize_money

logger = logging.getLogger("agentcart.agent.constraints")


class ConstraintEngine:
    """
    Deterministic Hard-Constraint Engine for autonomous shopping product candidate verification.
    """

    @classmethod
    def evaluate_candidate(
        cls,
        candidate: NormalizedProductCandidate,
        intent: ShoppingIntent
    ) -> ConstraintEvaluationResult:
        """
        Runs the full deterministic verification checklist on a candidate.
        Full evaluation mode collects all violations and returns a structured ConstraintEvaluationResult.
        """
        passed_rules: List[str] = []
        failed_rules: List[str] = []
        violations: List[ConstraintViolation] = []
        evaluated_constraints: List[str] = []
        unknown_constraints: List[str] = []
        soft_penalties: List[str] = []

        # 1. Step 1: Product Data Validity & Security Boundaries
        evaluated_constraints.append("DATA_VALIDITY")
        if not candidate.product_id or not candidate.id:
            msg = "Missing required authoritative product or candidate identifier"
            failed_rules.append(msg)
            violations.append(ConstraintViolation(
                constraint="DATA_VALIDITY",
                reason_code="INVALID_PRODUCT_DATA",
                message=msg
            ))

        if candidate.current_price is None or candidate.current_price < Decimal("0.00"):
            msg = f"Invalid or negative current_price: {candidate.current_price}"
            failed_rules.append(msg)
            violations.append(ConstraintViolation(
                constraint="DATA_VALIDITY",
                reason_code="INVALID_PRODUCT_DATA",
                message=msg,
                actual=str(candidate.current_price)
            ))

        if candidate.rating < 0.0 or candidate.rating > 5.0:
            msg = f"Invalid rating out of bounds [0.0, 5.0]: {candidate.rating}"
            failed_rules.append(msg)
            violations.append(ConstraintViolation(
                constraint="DATA_VALIDITY",
                reason_code="INVALID_RATING",
                message=msg,
                actual=candidate.rating
            ))

        # 2. Step 2: Currency Compatibility
        evaluated_constraints.append("CURRENCY")
        if candidate.currency != intent.currency:
            msg = f"Currency mismatch: product is in {candidate.currency}, required {intent.currency}"
            failed_rules.append(msg)
            violations.append(ConstraintViolation(
                constraint="CURRENCY",
                reason_code="CURRENCY_MISMATCH",
                message=msg,
                expected=intent.currency,
                actual=candidate.currency
            ))
        else:
            passed_rules.append(f"Currency matches {intent.currency}")

        # 3. Step 3: Hard Merchant Restriction (if explicitly required as a hard constraint)
        evaluated_constraints.append("MERCHANT")
        hard_merchant_constraints = [
            c for c in intent.spec_constraints 
            if c.key == "merchant" and c.is_hard_constraint and isinstance(c.target_value, str)
        ]
        for mc in hard_merchant_constraints:
            if candidate.merchant_code.upper() != mc.target_value.upper():
                msg = f"Merchant '{candidate.merchant_code}' does not match required '{mc.target_value}'"
                failed_rules.append(msg)
                violations.append(ConstraintViolation(
                    constraint="MERCHANT",
                    reason_code="MERCHANT_NOT_ALLOWED",
                    message=msg,
                    expected=mc.target_value.upper(),
                    actual=candidate.merchant_code.upper()
                ))
            else:
                passed_rules.append(f"Merchant '{candidate.merchant_code}' matches required '{mc.target_value}'")

        # 4. Step 4: Availability & Stock Fulfillment
        evaluated_constraints.append("AVAILABILITY")
        if intent.require_in_stock:
            if not candidate.in_stock or candidate.inventory_state == AvailabilityState.OUT_OF_STOCK:
                msg = "Product is out of stock across merchant warehouses"
                failed_rules.append(msg)
                violations.append(ConstraintViolation(
                    constraint="AVAILABILITY",
                    reason_code="OUT_OF_STOCK",
                    message=msg,
                    expected="IN_STOCK",
                    actual=candidate.inventory_state.value if hasattr(candidate.inventory_state, "value") else str(candidate.inventory_state)
                ))
            elif intent.quantity > 1 and candidate.available_quantity < intent.quantity:
                msg = f"Available quantity ({candidate.available_quantity}) is less than requested quantity ({intent.quantity})"
                failed_rules.append(msg)
                violations.append(ConstraintViolation(
                    constraint="AVAILABILITY",
                    reason_code="INSUFFICIENT_STOCK",
                    message=msg,
                    expected=intent.quantity,
                    actual=candidate.available_quantity
                ))
            else:
                passed_rules.append(f"In stock (Available: {candidate.available_quantity} units)")

        # 5. Step 5: Exact Decimal Budget Boundaries
        # A. Maximum Budget Gate
        evaluated_constraints.append("BUDGET_MAX")
        if intent.budget_max is not None:
            max_b = quantize_money(intent.budget_max)
            if candidate.current_price > max_b:
                msg = f"Price ₹{candidate.current_price:,.2f} exceeds maximum budget ₹{max_b:,.2f}"
                failed_rules.append(msg)
                violations.append(ConstraintViolation(
                    constraint="BUDGET_MAX",
                    reason_code="PRICE_ABOVE_MAX",
                    message=msg,
                    expected=str(max_b),
                    actual=str(candidate.current_price)
                ))
            else:
                passed_rules.append(f"Within budget (₹{candidate.current_price:,.2f} <= ₹{max_b:,.2f})")

        # B. Minimum Budget Filter
        evaluated_constraints.append("BUDGET_MIN")
        if intent.budget_min is not None:
            min_b = quantize_money(intent.budget_min)
            if candidate.current_price < min_b:
                msg = f"Price ₹{candidate.current_price:,.2f} is below minimum threshold ₹{min_b:,.2f}"
                failed_rules.append(msg)
                violations.append(ConstraintViolation(
                    constraint="BUDGET_MIN",
                    reason_code="PRICE_BELOW_MIN",
                    message=msg,
                    expected=str(min_b),
                    actual=str(candidate.current_price)
                ))
            else:
                passed_rules.append(f"Above minimum price filter (₹{candidate.current_price:,.2f})")

        # 6. Step 6: Technical Specifications
        for constraint in intent.spec_constraints:
            # Skip merchant key handled in Step 3
            if constraint.key == "merchant":
                continue

            spec_key = constraint.key
            evaluated_constraints.append(f"SPEC_{spec_key.upper()}")
            
            # Special case for RAM
            if spec_key == "ram_gb":
                cls._eval_ram_constraint(candidate, constraint, passed_rules, failed_rules, violations, unknown_constraints, soft_penalties)
            # Special case for Storage / SSD
            elif spec_key in ("ssd_gb", "storage_gb"):
                cls._eval_storage_constraint(candidate, constraint, passed_rules, failed_rules, violations, unknown_constraints, soft_penalties)
            # Special case for GPU
            elif spec_key == "gpu":
                cls._eval_gpu_constraint(candidate, constraint, passed_rules, failed_rules, violations, unknown_constraints, soft_penalties)
            # Special case for Brand
            elif spec_key == "brand":
                cls._eval_brand_constraint(candidate, constraint, passed_rules, failed_rules, violations, unknown_constraints, soft_penalties)
            # Special case for Rating
            elif spec_key == "rating":
                cls._eval_rating_constraint(candidate, constraint, passed_rules, failed_rules, violations, unknown_constraints, soft_penalties)
            # Generic binary operator
            else:
                cls._eval_generic_constraint(candidate, constraint, passed_rules, failed_rules, violations, unknown_constraints, soft_penalties)

        # 7. Step 7: Required Keywords
        combined_text = f"{candidate.title} {candidate.brand} {candidate.model or ''} {' '.join(str(v) for v in candidate.specs.values())}".lower()
        if intent.required_keywords:
            evaluated_constraints.append("REQUIRED_KEYWORDS")
            for kw in intent.required_keywords:
                if kw.lower() not in combined_text:
                    msg = f"Missing required keyword: '{kw}'"
                    failed_rules.append(msg)
                    violations.append(ConstraintViolation(
                        constraint="REQUIRED_KEYWORDS",
                        reason_code="MISSING_REQUIRED_KEYWORD",
                        message=msg,
                        expected=kw
                    ))
                else:
                    passed_rules.append(f"Contains required keyword: '{kw}'")

        # 8. Step 8: Excluded Keywords & Conditions (Fail-closed)
        if intent.excluded_keywords:
            evaluated_constraints.append("EXCLUSIONS")
            for kw in intent.excluded_keywords:
                if kw.lower() in combined_text:
                    msg = f"Contains excluded keyword or condition: '{kw}'"
                    failed_rules.append(msg)
                    violations.append(ConstraintViolation(
                        constraint="EXCLUSIONS",
                        reason_code="EXCLUDED_CONDITION" if kw.lower() in ("refurbished", "used", "renewed") else "CONTAINS_EXCLUDED_KEYWORD",
                        message=msg,
                        actual=kw
                    ))

        # 9. Step 9: Soft Preferences (Never fail candidate, only record soft penalties)
        if candidate.rating < intent.min_rating:
            soft_penalties.append(f"Merchant rating {candidate.rating} is below preferred {intent.min_rating}")
        else:
            passed_rules.append(f"Merchant rating {candidate.rating} >= {intent.min_rating}")

        if intent.merchant_preferences and candidate.merchant_code not in intent.merchant_preferences:
            soft_penalties.append(f"Merchant {candidate.merchant_code} is not in user preferred merchants {intent.merchant_preferences}")

        if intent.brand_preferences and candidate.brand.upper() not in [b.upper() for b in intent.brand_preferences]:
            soft_penalties.append(f"Brand '{candidate.brand}' is not in user preferred brands {intent.brand_preferences}")

        passed_all = len(failed_rules) == 0 and len(violations) == 0

        return ConstraintEvaluationResult(
            candidate_id=candidate.id,
            product_id=candidate.product_id,
            merchant_code=candidate.merchant_code,
            passed_all_hard_constraints=passed_all,
            passed=passed_all,
            violations=violations,
            passed_constraints=passed_rules,
            failed_constraints=failed_rules,
            unknown_constraints=unknown_constraints,
            soft_penalties=soft_penalties
        )

    @classmethod
    def evaluate_product(
        cls,
        candidate: NormalizedProductCandidate,
        intent: ShoppingIntent
    ) -> ConstraintEvaluationResult:
        """Alias for evaluate_candidate for standard product evaluation."""
        return cls.evaluate_candidate(candidate, intent)

    @classmethod
    def filter_candidates(
        cls,
        candidates: List[NormalizedProductCandidate],
        intent: ShoppingIntent
    ) -> Tuple[List[NormalizedProductCandidate], List[Tuple[NormalizedProductCandidate, List[str]]]]:
        """
        Partitions candidates into passing candidates and rejected candidates with reasons.
        """
        passing: List[NormalizedProductCandidate] = []
        rejected: List[Tuple[NormalizedProductCandidate, List[str]]] = []

        for c in candidates:
            res = cls.evaluate_candidate(c, intent)
            if res.passed_all_hard_constraints:
                passing.append(c)
            else:
                rejected.append((c, res.failed_constraints))

        return passing, rejected

    @classmethod
    def filter_products(
        cls,
        candidates: List[NormalizedProductCandidate],
        intent: ShoppingIntent
    ) -> ConstraintFilterResult:
        """
        Executes full deterministic constraint filtering and returns structured ConstraintFilterResult.
        """
        start_time = time.perf_counter()
        passed_candidates: List[NormalizedProductCandidate] = []
        rejected_candidates: List[NormalizedProductCandidate] = []
        evaluations: List[ConstraintEvaluationResult] = []
        rejection_summary: Dict[str, int] = {}

        for c in candidates:
            ev = cls.evaluate_candidate(c, intent)
            evaluations.append(ev)
            if ev.passed_all_hard_constraints:
                passed_candidates.append(c)
            else:
                rejected_candidates.append(c)
                for v in ev.violations:
                    rejection_summary[v.reason_code] = rejection_summary.get(v.reason_code, 0) + 1

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        logger.info(
            "Constraint filtering completed. %d passed, %d rejected out of %d total candidates.",
            len(passed_candidates), len(rejected_candidates), len(candidates)
        )

        return ConstraintFilterResult(
            total_input=len(candidates),
            total_passed=len(passed_candidates),
            total_rejected=len(rejected_candidates),
            passed_candidates=passed_candidates,
            rejected_candidates=rejected_candidates,
            evaluations=evaluations,
            rejection_summary=rejection_summary,
            execution_time_ms=elapsed_ms
        )

    # ------------------------------------------------------------------
    # Spec Constraint Helpers
    # ------------------------------------------------------------------

    @classmethod
    def _eval_ram_constraint(
        cls,
        candidate: NormalizedProductCandidate,
        constraint: SpecificationConstraint,
        passed_rules: List[str],
        failed_rules: List[str],
        violations: List[ConstraintViolation],
        unknown_constraints: List[str],
        soft_penalties: List[str]
    ) -> None:
        actual_val = candidate.specs.get("ram_gb")
        if actual_val is None:
            if constraint.is_hard_constraint:
                unknown_constraints.append("ram_gb")
                msg = "Specification 'ram_gb' not specified by merchant"
                failed_rules.append(msg)
                violations.append(ConstraintViolation(
                    constraint="RAM_GB",
                    reason_code="UNKNOWN_REQUIRED_ATTRIBUTE",
                    message=msg,
                    expected=constraint.target_value
                ))
            else:
                soft_penalties.append("RAM capacity not specified by merchant")
            return

        try:
            act_num = int(actual_val)
            tgt_num = int(constraint.target_value)
            if act_num >= tgt_num:
                passed_rules.append(f"Specification 'ram_gb' ({actual_val}) >= {constraint.target_value}")
            else:
                msg = f"Specification 'ram_gb' ({actual_val}) is less than required {constraint.target_value}"
                if constraint.is_hard_constraint:
                    failed_rules.append(msg)
                    violations.append(ConstraintViolation(
                        constraint="RAM_GB",
                        reason_code="RAM_BELOW_MIN",
                        message=msg,
                        expected=tgt_num,
                        actual=act_num
                    ))
                else:
                    soft_penalties.append(msg)
        except (ValueError, TypeError):
            msg = f"Malformed RAM specification: {actual_val}"
            if constraint.is_hard_constraint:
                failed_rules.append(msg)
                violations.append(ConstraintViolation(
                    constraint="RAM_GB",
                    reason_code="MALFORMED_SPECIFICATION",
                    message=msg,
                    actual=actual_val
                ))

    @classmethod
    def _eval_storage_constraint(
        cls,
        candidate: NormalizedProductCandidate,
        constraint: SpecificationConstraint,
        passed_rules: List[str],
        failed_rules: List[str],
        violations: List[ConstraintViolation],
        unknown_constraints: List[str],
        soft_penalties: List[str]
    ) -> None:
        actual_val = candidate.specs.get("ssd_gb") or candidate.specs.get("storage_gb")
        if actual_val is None:
            if constraint.is_hard_constraint:
                unknown_constraints.append("ssd_gb")
                msg = "Specification 'ssd_gb' not specified by merchant"
                failed_rules.append(msg)
                violations.append(ConstraintViolation(
                    constraint="STORAGE_GB",
                    reason_code="UNKNOWN_REQUIRED_ATTRIBUTE",
                    message=msg,
                    expected=constraint.target_value
                ))
            else:
                soft_penalties.append("Storage capacity not specified by merchant")
            return

        try:
            act_num = int(actual_val)
            tgt_num = int(constraint.target_value)
            if act_num >= tgt_num:
                passed_rules.append(f"Specification 'ssd_gb' ({actual_val}) >= {constraint.target_value}")
            else:
                msg = f"Specification 'ssd_gb' ({actual_val}) is less than required {constraint.target_value}"
                if constraint.is_hard_constraint:
                    failed_rules.append(msg)
                    violations.append(ConstraintViolation(
                        constraint="STORAGE_GB",
                        reason_code="STORAGE_BELOW_MIN",
                        message=msg,
                        expected=tgt_num,
                        actual=act_num
                    ))
                else:
                    soft_penalties.append(msg)
        except (ValueError, TypeError):
            msg = f"Malformed storage specification: {actual_val}"
            if constraint.is_hard_constraint:
                failed_rules.append(msg)
                violations.append(ConstraintViolation(
                    constraint="STORAGE_GB",
                    reason_code="MALFORMED_SPECIFICATION",
                    message=msg,
                    actual=actual_val
                ))

    @classmethod
    def _eval_gpu_constraint(
        cls,
        candidate: NormalizedProductCandidate,
        constraint: SpecificationConstraint,
        passed_rules: List[str],
        failed_rules: List[str],
        violations: List[ConstraintViolation],
        unknown_constraints: List[str],
        soft_penalties: List[str]
    ) -> None:
        actual_gpu = candidate.specs.get("gpu")
        target_req = str(constraint.target_value).strip().lower()

        if not actual_gpu:
            if constraint.is_hard_constraint:
                unknown_constraints.append("gpu")
                msg = "GPU specification not specified by merchant"
                failed_rules.append(msg)
                violations.append(ConstraintViolation(
                    constraint="GPU",
                    reason_code="UNKNOWN_REQUIRED_ATTRIBUTE",
                    message=msg,
                    expected=constraint.target_value
                ))
            else:
                soft_penalties.append("GPU not specified")
            return

        act_lower = str(actual_gpu).lower()
        satisfied = False

        # Deterministic matching rules
        if "rtx" in target_req:
            # Requires NVIDIA RTX series
            if "rtx" in act_lower:
                # If specific model requested e.g. "rtx 4070"
                req_model = re.search(r'rtx\s*(\d{4})', target_req)
                if req_model:
                    act_model = re.search(r'rtx\s*(\d{4})', act_lower)
                    if act_model and int(act_model.group(1)) >= int(req_model.group(1)):
                        satisfied = True
                else:
                    satisfied = True
        elif "gtx" in target_req:
            satisfied = "gtx" in act_lower or "rtx" in act_lower
        elif "apple" in target_req or "m3" in target_req or "m4" in target_req:
            satisfied = any(term in act_lower for term in ("m3", "m4", "apple"))
        elif "radeon" in target_req or "amd" in target_req:
            satisfied = "radeon" in act_lower or "amd" in act_lower
        else:
            satisfied = target_req in act_lower

        if satisfied:
            passed_rules.append(f"GPU '{actual_gpu}' satisfies required '{constraint.target_value}'")
        else:
            msg = f"GPU '{actual_gpu}' does not satisfy requirement '{constraint.target_value}'"
            if constraint.is_hard_constraint:
                failed_rules.append(msg)
                violations.append(ConstraintViolation(
                    constraint="GPU",
                    reason_code="GPU_REQUIREMENT_NOT_MET",
                    message=msg,
                    expected=constraint.target_value,
                    actual=actual_gpu
                ))
            else:
                soft_penalties.append(msg)

    @classmethod
    def _eval_brand_constraint(
        cls,
        candidate: NormalizedProductCandidate,
        constraint: SpecificationConstraint,
        passed_rules: List[str],
        failed_rules: List[str],
        violations: List[ConstraintViolation],
        unknown_constraints: List[str],
        soft_penalties: List[str]
    ) -> None:
        target_brand = str(constraint.target_value).strip().lower()
        actual_brand = candidate.brand.strip().lower()
        if actual_brand == target_brand:
            passed_rules.append(f"Brand '{candidate.brand}' matches required '{constraint.target_value}'")
        else:
            msg = f"Brand '{candidate.brand}' does not match required '{constraint.target_value}'"
            if constraint.is_hard_constraint:
                failed_rules.append(msg)
                violations.append(ConstraintViolation(
                    constraint="BRAND",
                    reason_code="BRAND_NOT_ALLOWED",
                    message=msg,
                    expected=constraint.target_value,
                    actual=candidate.brand
                ))
            else:
                soft_penalties.append(msg)

    @classmethod
    def _eval_rating_constraint(
        cls,
        candidate: NormalizedProductCandidate,
        constraint: SpecificationConstraint,
        passed_rules: List[str],
        failed_rules: List[str],
        violations: List[ConstraintViolation],
        unknown_constraints: List[str],
        soft_penalties: List[str]
    ) -> None:
        try:
            target_rating = float(constraint.target_value)
            if candidate.rating >= target_rating:
                passed_rules.append(f"Rating {candidate.rating} >= {target_rating}")
            else:
                msg = f"Rating {candidate.rating} is below required {target_rating}"
                if constraint.is_hard_constraint:
                    failed_rules.append(msg)
                    violations.append(ConstraintViolation(
                        constraint="RATING",
                        reason_code="RATING_BELOW_MIN",
                        message=msg,
                        expected=target_rating,
                        actual=candidate.rating
                    ))
                else:
                    soft_penalties.append(msg)
        except (ValueError, TypeError):
            pass

    @classmethod
    def _eval_generic_constraint(
        cls,
        candidate: NormalizedProductCandidate,
        constraint: SpecificationConstraint,
        passed_rules: List[str],
        failed_rules: List[str],
        violations: List[ConstraintViolation],
        unknown_constraints: List[str],
        soft_penalties: List[str]
    ) -> None:
        spec_key = constraint.key
        actual_val = candidate.specs.get(spec_key)

        is_satisfied, reason = cls._check_operator(spec_key, actual_val, constraint.operator, constraint.target_value)
        if is_satisfied:
            passed_rules.append(reason)
        else:
            if actual_val is None:
                unknown_constraints.append(spec_key)
                if constraint.is_hard_constraint:
                    failed_rules.append(reason)
                    violations.append(ConstraintViolation(
                        constraint=spec_key.upper(),
                        reason_code="UNKNOWN_REQUIRED_ATTRIBUTE",
                        message=reason,
                        expected=constraint.target_value
                    ))
                else:
                    soft_penalties.append(reason)
            else:
                if constraint.is_hard_constraint:
                    failed_rules.append(reason)
                    violations.append(ConstraintViolation(
                        constraint=spec_key.upper(),
                        reason_code="SPECIFICATION_MISMATCH",
                        message=reason,
                        expected=constraint.target_value,
                        actual=actual_val
                    ))
                else:
                    soft_penalties.append(reason)

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
