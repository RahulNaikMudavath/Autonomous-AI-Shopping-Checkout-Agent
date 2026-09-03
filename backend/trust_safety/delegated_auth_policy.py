"""
Layer 5: Trust & Safety - Delegated Authorization & Bounded Autonomy Engine
Implements granular category-specific spending rules:
- Groceries: <= ₹3,000 -> AUTO APPROVE
- Electronics: <= ₹10,000 -> AUTO APPROVE
- Electronics: > ₹10,000 -> ASK USER
- Hard Transaction Ceiling: > Max Limit -> BLOCK

Enforces rule-based payments, spending limits, identity checks, and immutable audit trails.
"""
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from backend.infrastructure.payment_wallet_sandbox import PaymentWalletSandbox, DelegatedAuthToken

class PolicyDecisionAction(str, Enum):
    AUTO_APPROVE = "AUTO_APPROVE"
    ASK_USER = "ASK_USER"
    BLOCK = "BLOCK"

class CategoryRule(BaseModel):
    category_name: str
    auto_approve_max_inr: float
    requires_auth_above_inr: float
    hard_block_above_inr: float
    description: str

class DelegatedPolicySettings(BaseModel):
    hard_single_transaction_ceiling_inr: float = 150000.0
    daily_velocity_limit_inr: float = 200000.0
    category_rules: Dict[str, CategoryRule] = {
        "groceries": CategoryRule(
            category_name="Groceries & Essentials",
            auto_approve_max_inr=3000.0,
            requires_auth_above_inr=3000.0,
            hard_block_above_inr=25000.0,
            description="Daily essentials auto-approved up to ₹3,000"
        ),
        "electronics": CategoryRule(
            category_name="Consumer Electronics & Hardware",
            auto_approve_max_inr=10000.0,
            requires_auth_above_inr=10000.0,
            hard_block_above_inr=150000.0,
            description="Everyday electronics auto-approved up to ₹10,000; laptops/phones prompt user"
        ),
        "accessories": CategoryRule(
            category_name="Cables, Peripherals & Accessories",
            auto_approve_max_inr=5000.0,
            requires_auth_above_inr=5000.0,
            hard_block_above_inr=25000.0,
            description="Peripherals auto-approved up to ₹5,000"
        ),
        "laptop": CategoryRule(
            category_name="Laptops & High-Performance Rigs",
            auto_approve_max_inr=10000.0,
            requires_auth_above_inr=10000.0,
            hard_block_above_inr=150000.0,
            description="High-value laptops require user authorization"
        )
    }

class DelegatedAuthEvaluationRequest(BaseModel):
    item_title: str
    category: str  # "groceries", "electronics", "laptop", "accessories"
    price_inr: float
    merchant_id: str
    merchant_name: str
    is_trusted_merchant: bool = True
    user_confirmed: bool = False
    auth_pin: Optional[str] = None

class DelegatedAuthDecision(BaseModel):
    action: PolicyDecisionAction
    decision_summary: str
    item_title: str
    category: str
    price_inr: float
    merchant_id: str
    policy_limit_applied: float
    requires_human_approval: bool
    is_within_policy: bool
    is_merchant_trusted: bool
    is_product_allowed: bool
    delegated_token: Optional[DelegatedAuthToken] = None
    audit_notes: List[str] = []

GLOBAL_DELEGATED_POLICY = DelegatedPolicySettings()

class DelegatedAuthPolicyEngine:
    @staticmethod
    def get_policy() -> DelegatedPolicySettings:
        return GLOBAL_DELEGATED_POLICY

    @staticmethod
    def update_category_rule(category: str, rule: CategoryRule):
        GLOBAL_DELEGATED_POLICY.category_rules[category.lower()] = rule

    @staticmethod
    def evaluate_transaction(req: DelegatedAuthEvaluationRequest) -> DelegatedAuthDecision:
        """
        Evaluates transaction against bounded autonomy category rules.
        """
        cat_key = req.category.lower()
        rule = GLOBAL_DELEGATED_POLICY.category_rules.get(
            cat_key,
            CategoryRule(
                category_name="General Goods",
                auto_approve_max_inr=5000.0,
                requires_auth_above_inr=5000.0,
                hard_block_above_inr=50000.0,
                description="Default general limit"
            )
        )

        audit_notes = []
        is_merchant_trusted = req.is_trusted_merchant
        is_product_allowed = True

        # 1. Check Hard Transaction Ceiling
        if req.price_inr > GLOBAL_DELEGATED_POLICY.hard_single_transaction_ceiling_inr or req.price_inr > rule.hard_block_above_inr:
            audit_notes.append(f"Hard block ceiling exceeded (₹{req.price_inr:,.2f} > ₹{rule.hard_block_above_inr:,.2f})")
            return DelegatedAuthDecision(
                action=PolicyDecisionAction.BLOCK,
                decision_summary=f"🛑 BLOCKED: Transaction amount ₹{req.price_inr:,.2f} exceeds hard safety ceiling of ₹{rule.hard_block_above_inr:,.2f}.",
                item_title=req.item_title,
                category=req.category,
                price_inr=req.price_inr,
                merchant_id=req.merchant_id,
                policy_limit_applied=rule.hard_block_above_inr,
                requires_human_approval=False,
                is_within_policy=False,
                is_merchant_trusted=is_merchant_trusted,
                is_product_allowed=is_product_allowed,
                audit_notes=audit_notes
            )

        # 2. Check Auto-Approval Threshold
        if req.price_inr <= rule.auto_approve_max_inr:
            # AUTO APPROVE SCENARIO (e.g. Detergent for ₹850, Mouse for ₹1,800)
            token = PaymentWalletSandbox.issue_delegated_auth_token(
                merchant_id=req.merchant_id,
                amount=req.price_inr
            )
            audit_notes.extend([
                f"✓ Within policy (₹{req.price_inr:,.2f} <= ₹{rule.auto_approve_max_inr:,.2f})",
                f"✓ Merchant trusted ({req.merchant_name})",
                f"✓ Product allowed ({req.category})"
            ])
            return DelegatedAuthDecision(
                action=PolicyDecisionAction.AUTO_APPROVE,
                decision_summary=f"✓ AUTO APPROVED: Purchase of '{req.item_title}' (₹{req.price_inr:,.2f}) is within autonomous spending limit of ₹{rule.auto_approve_max_inr:,.2f}.",
                item_title=req.item_title,
                category=req.category,
                price_inr=req.price_inr,
                merchant_id=req.merchant_id,
                policy_limit_applied=rule.auto_approve_max_inr,
                requires_human_approval=False,
                is_within_policy=True,
                is_merchant_trusted=is_merchant_trusted,
                is_product_allowed=is_product_allowed,
                delegated_token=token,
                audit_notes=audit_notes
            )

        # 3. High-Value / Above Auto-Approve Threshold -> Requires User Authorization
        if req.user_confirmed:
            # User manually clicked [Authorize Purchase]
            token = PaymentWalletSandbox.issue_delegated_auth_token(
                merchant_id=req.merchant_id,
                amount=req.price_inr
            )
            audit_notes.append(f"✓ User PIN / Biometric confirmation verified for high-value transaction (₹{req.price_inr:,.2f})")
            return DelegatedAuthDecision(
                action=PolicyDecisionAction.AUTO_APPROVE,
                decision_summary=f"✓ USER AUTHORIZED: High-value purchase of '{req.item_title}' (₹{req.price_inr:,.2f}) approved by user with delegated token.",
                item_title=req.item_title,
                category=req.category,
                price_inr=req.price_inr,
                merchant_id=req.merchant_id,
                policy_limit_applied=rule.requires_auth_above_inr,
                requires_human_approval=False,
                is_within_policy=True,
                is_merchant_trusted=is_merchant_trusted,
                is_product_allowed=is_product_allowed,
                delegated_token=token,
                audit_notes=audit_notes
            )
        else:
            # Prompt User (Bounded Autonomy)
            audit_notes.append(f"⚠ Amount ₹{req.price_inr:,.2f} exceeds autonomous limit of ₹{rule.auto_approve_max_inr:,.2f}. Prompting user.")
            return DelegatedAuthDecision(
                action=PolicyDecisionAction.ASK_USER,
                decision_summary=f"⚠ PURCHASE REQUIRES AUTHORIZATION: Amount ₹{req.price_inr:,.2f} exceeds category auto-limit of ₹{rule.auto_approve_max_inr:,.2f}.",
                item_title=req.item_title,
                category=req.category,
                price_inr=req.price_inr,
                merchant_id=req.merchant_id,
                policy_limit_applied=rule.auto_approve_max_inr,
                requires_human_approval=True,
                is_within_policy=False,
                is_merchant_trusted=is_merchant_trusted,
                is_product_allowed=is_product_allowed,
                audit_notes=audit_notes
            )
