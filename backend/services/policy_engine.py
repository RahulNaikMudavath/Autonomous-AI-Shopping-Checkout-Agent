"""
Phase 5 — Step 1: Deterministic Purchase Policy Engine Service
Coordinates server-authoritative evaluation of checkout quotes against spending,
merchant, category, quantity, shipping, and security guardrails.
Produces deterministic decisions: ALLOW, REQUIRE_AUTHORIZATION, or DENY.
Zero payment execution, zero order creation, zero state mutation.
"""
from datetime import datetime, timezone
from decimal import Decimal
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload

from backend.database.models import (
    PurchasePolicyModel, PolicyEvaluationRecordModel,
    CheckoutSessionModel, CartModel, ProductModel, MerchantModel, ShippingOptionModel
)
from backend.domain.marketplace import (
    PolicyDecisionType, PolicyEvaluationResponse, PurchasePolicyDetail
)
from backend.core.errors import AgentCartException, EntityNotFoundException
from backend.services.inventory_service import InventoryService
from backend.services.pricing_service import quantize_money

logger = logging.getLogger("agentcart.policy.engine")

# Categories classified as fail-closed / high-risk
DEFAULT_BLOCKED_CATEGORIES = ["WEAPONS", "TOBACCO", "HAZARDOUS", "ILLEGAL_GOODS"]

DENY_REASON_CODES = {
    "INVALID_QUOTE",
    "EXPIRED_QUOTE",
    "INVALID_CART",
    "STALE_CART",
    "PRICE_CHANGED",
    "INSUFFICIENT_INVENTORY",
    "OUT_OF_STOCK",
    "INACTIVE_MERCHANT",
    "INACTIVE_PRODUCT",
    "POLICY_INACTIVE",
    "MISSING_POLICY",
    "BLOCKED_PRODUCT_ID",
    "BLOCKED_SKU",
    "BLOCKED_MERCHANT",
    "UNAUTHORIZED_MERCHANT",
    "BLOCKED_CATEGORY",
    "UNKNOWN_CATEGORY_FAIL_CLOSED",
    "UNAUTHORIZED_CATEGORY",
    "EXCEEDS_MAX_PRODUCT_QUANTITY",
    "EXCEEDS_MAX_TOTAL_QUANTITY",
    "EXCEEDS_MAX_SHIPPING_COST",
    "BLOCKED_SHIPPING_TYPE",
    "UNAUTHORIZED_SHIPPING_TYPE",
    "EXCEEDS_MAX_PURCHASE_AMOUNT",
}

REQUIRE_AUTH_REASON_CODES = {
    "ABOVE_AUTO_APPROVAL_THRESHOLD"
}


def generate_policy_explanation(
    decision: PolicyDecisionType,
    reason_codes: List[str],
    grand_total: Decimal,
    policy: PurchasePolicyModel
) -> str:
    """Generates a structured, deterministic human-readable explanation from evaluated reason codes."""
    if decision == PolicyDecisionType.ALLOW:
        return (
            f"Purchase of ₹{grand_total:,.2f} is fully allowed by policy '{policy.name}' (v{policy.version}). "
            f"Amount is within the auto-approval threshold of ₹{policy.auto_approval_limit:,.2f}."
        )
    
    if decision == PolicyDecisionType.REQUIRE_AUTHORIZATION:
        return (
            f"Human authorization required: Grand total ₹{grand_total:,.2f} exceeds automatic approval limit "
            f"of ₹{policy.auto_approval_limit:,.2f} (Policy: '{policy.name}' v{policy.version})."
        )
    
    # DENY explanations
    reasons_text = []
    for code in reason_codes:
        if code == "EXCEEDS_MAX_PURCHASE_AMOUNT":
            reasons_text.append(f"Grand total ₹{grand_total:,.2f} exceeds maximum purchase limit of ₹{policy.max_purchase_amount:,.2f}")
        elif code == "BLOCKED_MERCHANT":
            reasons_text.append("Merchant is explicitly blocked by purchase policy")
        elif code == "UNAUTHORIZED_MERCHANT":
            reasons_text.append("Merchant is not in the allowed merchants allowlist")
        elif code == "BLOCKED_CATEGORY":
            reasons_text.append("Contains item in a restricted product category")
        elif code == "UNKNOWN_CATEGORY_FAIL_CLOSED":
            reasons_text.append("Product category could not be authoritatively established (failed closed)")
        elif code == "UNAUTHORIZED_CATEGORY":
            reasons_text.append("Contains item not in the permitted categories allowlist")
        elif code == "BLOCKED_PRODUCT_ID":
            reasons_text.append("Contains a blocked product ID")
        elif code == "BLOCKED_SKU":
            reasons_text.append("Contains a blocked product SKU")
        elif code == "EXCEEDS_MAX_PRODUCT_QUANTITY":
            reasons_text.append(f"Quantity for an item exceeds maximum per-product limit of {policy.max_quantity_per_product}")
        elif code == "EXCEEDS_MAX_TOTAL_QUANTITY":
            reasons_text.append(f"Total cart quantity exceeds maximum overall limit of {policy.max_total_quantity}")
        elif code == "EXCEEDS_MAX_SHIPPING_COST":
            reasons_text.append(f"Shipping cost exceeds maximum allowed shipping limit of ₹{policy.max_shipping_cost:,.2f}")
        elif code == "BLOCKED_SHIPPING_TYPE":
            reasons_text.append("Selected shipping delivery type is prohibited")
        elif code == "UNAUTHORIZED_SHIPPING_TYPE":
            reasons_text.append("Selected shipping delivery type is not in the allowed shipping types")
        elif code == "POLICY_INACTIVE":
            reasons_text.append(f"Purchase policy '{policy.name}' is currently inactive")
        elif code == "EXPIRED_QUOTE":
            reasons_text.append("Checkout quote has expired")
        elif code == "STALE_CART":
            reasons_text.append("Cart contents mutated after quote generation (stale quote)")
        elif code == "PRICE_CHANGED":
            reasons_text.append("Catalog price has changed since quote generation")
        elif code == "INSUFFICIENT_INVENTORY":
            reasons_text.append("Live inventory is insufficient to fulfill quote")
        elif code == "INACTIVE_MERCHANT":
            reasons_text.append("Merchant is currently inactive")
        elif code == "INACTIVE_PRODUCT":
            reasons_text.append("One or more products in quote are no longer active")
        else:
            reasons_text.append(code.replace("_", " ").lower())
            
    return f"Purchase blocked by policy: {'; '.join(reasons_text)}."


class PolicyEngine:
    """
    Server-authoritative, deterministic purchase policy evaluation engine.
    """

    @classmethod
    def get_or_create_default_policy(
        cls,
        db: Session,
        scope: str = "GLOBAL",
        scope_id: Optional[str] = None
    ) -> PurchasePolicyModel:
        """Retrieves active policy for given scope or initializes the safe default policy."""
        query = db.query(PurchasePolicyModel).filter(
            PurchasePolicyModel.policy_scope == scope
        )
        if scope_id:
            query = query.filter(PurchasePolicyModel.scope_id == scope_id)
        else:
            query = query.filter(PurchasePolicyModel.scope_id.is_(None))

        policy = query.order_by(PurchasePolicyModel.version.desc()).first()
        if not policy:
            policy = PurchasePolicyModel(
                name="Default Spending & Safety Policy",
                policy_scope=scope,
                scope_id=scope_id,
                version=1,
                is_active=True,
                max_purchase_amount=Decimal("100000.00"),
                auto_approval_limit=Decimal("25000.00"),
                allowed_merchants=[],
                blocked_merchants=[],
                allowed_categories=[],
                blocked_categories=DEFAULT_BLOCKED_CATEGORIES,
                blocked_product_ids=[],
                blocked_skus=[],
                max_quantity_per_product=10,
                max_total_quantity=25,
                max_shipping_cost=Decimal("500.00"),
                allowed_shipping_types=[],
                blocked_shipping_types=[]
            )
            db.add(policy)
            db.commit()
            db.refresh(policy)
            logger.info("Initialized default PurchasePolicy (id=%s, scope=%s, v=1)", policy.id, scope)

        return policy

    @classmethod
    def evaluate_quote_against_policy(
        cls,
        db: Session,
        quote_id: str,
        policy_id: Optional[str] = None,
        caller_session_id: Optional[str] = None
    ) -> PolicyEvaluationResponse:
        """
        Main entrypoint for deterministic policy evaluation.
        Evaluates authoritative checkout quote against a purchase policy.
        """
        now = datetime.now(timezone.utc)
        evaluated_rules: List[str] = []
        reason_codes: List[str] = []

        # 1. Fetch Authoritative Checkout Quote Session
        session = db.query(CheckoutSessionModel).options(
            joinedload(CheckoutSessionModel.cart),
            joinedload(CheckoutSessionModel.merchant)
        ).filter(CheckoutSessionModel.id == quote_id).first()

        if not session:
            raise EntityNotFoundException("CheckoutQuote", quote_id)

        # Enforce horizontal tenant/session isolation
        if caller_session_id and session.session_id and session.session_id != caller_session_id:
            logger.warning(
                "Horizontal access violation in policy engine: caller '%s' attempted to evaluate quote '%s' owned by '%s'",
                caller_session_id, session.id, session.session_id
            )
            raise AgentCartException(
                "Access denied: Checkout quote belongs to another user session.",
                code="UNAUTHORIZED_CHECKOUT_ACCESS",
                status_code=403,
                details={"quote_id": quote_id}
            )

        # 2. Fetch Policy
        if policy_id:
            policy = db.query(PurchasePolicyModel).filter(PurchasePolicyModel.id == policy_id).first()
            if not policy:
                raise EntityNotFoundException("PurchasePolicy", policy_id)
        else:
            policy = cls.get_or_create_default_policy(db, scope="GLOBAL")

        # Capture frozen policy snapshot
        policy_snapshot = policy.to_dict()

        # =====================================================================
        # RULE 0: Pre-requisite Quote Invariant Verification
        # =====================================================================
        evaluated_rules.append("RULE_QUOTE_INVARIANTS")
        
        # Expiration Check
        if session.status == "EXPIRED" or (session.expires_at and now > session.expires_at):
            reason_codes.append("EXPIRED_QUOTE")

        # Cart Integrity Check
        cart = session.cart or db.query(CartModel).filter(CartModel.id == session.cart_id).first()
        if not cart or cart.status != "ACTIVE":
            reason_codes.append("INVALID_CART")
        elif cart.updated_at and session.created_at and cart.updated_at > session.created_at:
            reason_codes.append("STALE_CART")

        # Merchant Integrity
        merchant = session.merchant or db.query(MerchantModel).filter(MerchantModel.id == session.merchant_id).first()
        if not merchant or not merchant.is_active:
            reason_codes.append("INACTIVE_MERCHANT")

        # Live Item & Catalog Verification
        items_snapshot = session.items_snapshot or []
        total_quantity = 0

        for item in items_snapshot:
            prod_id = item.get("product_id")
            sku = item.get("sku")
            qty = int(item.get("quantity", 1))
            unit_price_snapshot = Decimal(str(item.get("unit_price", "0.00")))
            total_quantity += qty

            prod = db.query(ProductModel).filter(ProductModel.id == prod_id).first()
            if not prod or not prod.is_active:
                reason_codes.append("INACTIVE_PRODUCT")
                continue

            # Live price check
            live_price = quantize_money(prod.current_price)
            if live_price != quantize_money(unit_price_snapshot):
                reason_codes.append("PRICE_CHANGED")

            # Live inventory check
            can_fulfill, avail_qty, _ = InventoryService.check_availability(db, prod.id, qty)
            if not can_fulfill:
                if avail_qty == 0:
                    reason_codes.append("OUT_OF_STOCK")
                else:
                    reason_codes.append("INSUFFICIENT_INVENTORY")

        # =====================================================================
        # RULE 1: Policy Active Status
        # =====================================================================
        evaluated_rules.append("RULE_POLICY_ACTIVE_CHECK")
        if not policy.is_active:
            reason_codes.append("POLICY_INACTIVE")

        # =====================================================================
        # RULE 2: Blocked Products & SKUs
        # =====================================================================
        evaluated_rules.append("RULE_BLOCKED_PRODUCTS_AND_SKUS")
        blocked_prod_ids = set(policy.blocked_product_ids or [])
        blocked_skus_set = {s.strip().upper() for s in (policy.blocked_skus or []) if s}

        for item in items_snapshot:
            prod_id = item.get("product_id")
            sku = str(item.get("sku", "")).strip().upper()
            if prod_id in blocked_prod_ids:
                reason_codes.append("BLOCKED_PRODUCT_ID")
            if sku in blocked_skus_set:
                reason_codes.append("BLOCKED_SKU")

        # =====================================================================
        # RULE 3: Merchant Allowlist & Blocklist
        # =====================================================================
        evaluated_rules.append("RULE_MERCHANT_PERMISSIONS")
        merchant_code = (merchant.merchant_code if merchant else "").strip().upper()
        blocked_merchants = {m.strip().upper() for m in (policy.blocked_merchants or []) if m}
        allowed_merchants = {m.strip().upper() for m in (policy.allowed_merchants or []) if m}

        if merchant_code in blocked_merchants:
            reason_codes.append("BLOCKED_MERCHANT")
        elif allowed_merchants and merchant_code not in allowed_merchants:
            reason_codes.append("UNAUTHORIZED_MERCHANT")

        # =====================================================================
        # RULE 4: Category Allowlist & Blocklist (Fail Closed)
        # =====================================================================
        evaluated_rules.append("RULE_CATEGORY_PERMISSIONS")
        blocked_categories = {c.strip().upper() for c in (policy.blocked_categories or []) if c}
        allowed_categories = {c.strip().upper() for c in (policy.allowed_categories or []) if c}

        for item in items_snapshot:
            prod_id = item.get("product_id")
            prod = db.query(ProductModel).filter(ProductModel.id == prod_id).first()
            raw_category = prod.category if prod else None
            
            if not raw_category or not str(raw_category).strip() or str(raw_category).strip().upper() in ["UNKNOWN", "NONE", "NULL"]:
                # Fail closed on missing/unknown category metadata
                reason_codes.append("UNKNOWN_CATEGORY_FAIL_CLOSED")
            else:
                cat_clean = str(raw_category).strip().upper()
                if cat_clean in blocked_categories:
                    reason_codes.append("BLOCKED_CATEGORY")
                elif allowed_categories and cat_clean not in allowed_categories:
                    reason_codes.append("UNAUTHORIZED_CATEGORY")

        # =====================================================================
        # RULE 5: Quantity Restrictions (Per-Product & Total)
        # =====================================================================
        evaluated_rules.append("RULE_QUANTITY_LIMITS")
        for item in items_snapshot:
            qty = int(item.get("quantity", 1))
            if policy.max_quantity_per_product and qty > policy.max_quantity_per_product:
                reason_codes.append("EXCEEDS_MAX_PRODUCT_QUANTITY")
                break

        if policy.max_total_quantity and total_quantity > policy.max_total_quantity:
            reason_codes.append("EXCEEDS_MAX_TOTAL_QUANTITY")

        # =====================================================================
        # RULE 6: Shipping Restrictions
        # =====================================================================
        evaluated_rules.append("RULE_SHIPPING_LIMITS")
        shipping_cost = Decimal(str(session.shipping_total or "0.00"))
        if policy.max_shipping_cost is not None and shipping_cost > policy.max_shipping_cost:
            reason_codes.append("EXCEEDS_MAX_SHIPPING_COST")

        if session.shipping_option_id:
            ship_opt = db.query(ShippingOptionModel).filter(ShippingOptionModel.id == session.shipping_option_id).first()
            if ship_opt:
                deliv_type = str(ship_opt.delivery_type or ship_opt.code or "").strip().upper()
                blocked_ship = {s.strip().upper() for s in (policy.blocked_shipping_types or []) if s}
                allowed_ship = {s.strip().upper() for s in (policy.allowed_shipping_types or []) if s}

                if deliv_type in blocked_ship:
                    reason_codes.append("BLOCKED_SHIPPING_TYPE")
                elif allowed_ship and deliv_type not in allowed_ship:
                    reason_codes.append("UNAUTHORIZED_SHIPPING_TYPE")

        # =====================================================================
        # RULE 7 & 8: Spending Limits & Auto-Approval Threshold
        # =====================================================================
        evaluated_rules.append("RULE_SPENDING_LIMITS")
        authoritative_grand_total = Decimal(str(session.grand_total))

        if policy.max_purchase_amount is not None and authoritative_grand_total > policy.max_purchase_amount:
            reason_codes.append("EXCEEDS_MAX_PURCHASE_AMOUNT")
        elif policy.auto_approval_limit is not None and authoritative_grand_total > policy.auto_approval_limit:
            reason_codes.append("ABOVE_AUTO_APPROVAL_THRESHOLD")

        # =====================================================================
        # FINAL DETERMINISTIC DECISION RESOLUTION
        # =====================================================================
        # Deduplicate reason codes while preserving order
        unique_reasons = list(dict.fromkeys(reason_codes))

        has_deny = any(r in DENY_REASON_CODES for r in unique_reasons)
        has_require_auth = any(r in REQUIRE_AUTH_REASON_CODES for r in unique_reasons)

        if has_deny:
            decision = PolicyDecisionType.DENY
        elif has_require_auth:
            decision = PolicyDecisionType.REQUIRE_AUTHORIZATION
        else:
            decision = PolicyDecisionType.ALLOW
            unique_reasons.append("ALL_RULES_PASSED")

        human_explanation = generate_policy_explanation(
            decision=decision,
            reason_codes=unique_reasons,
            grand_total=authoritative_grand_total,
            policy=policy
        )

        # =====================================================================
        # Persist Immutable Policy Evaluation Audit Record
        # =====================================================================
        audit_record = PolicyEvaluationRecordModel(
            quote_id=session.id,
            policy_id=policy.id,
            policy_version=policy.version,
            session_id=session.session_id,
            decision=decision.value,
            reason_codes=unique_reasons,
            evaluated_rules=evaluated_rules,
            grand_total=authoritative_grand_total,
            policy_snapshot=policy_snapshot,
            created_at=now
        )
        db.add(audit_record)
        db.commit()

        logger.info(
            "Policy evaluated for quote %s against policy %s (v%d): Decision=%s, Reasons=%s",
            session.id, policy.id, policy.version, decision.value, unique_reasons
        )

        return PolicyEvaluationResponse(
            decision=decision,
            reason_codes=unique_reasons,
            human_explanation=human_explanation,
            evaluated_rules=evaluated_rules,
            policy_id=policy.id,
            policy_version=policy.version,
            quote_id=session.id,
            grand_total=authoritative_grand_total,
            evaluated_at=now.isoformat()
        )
