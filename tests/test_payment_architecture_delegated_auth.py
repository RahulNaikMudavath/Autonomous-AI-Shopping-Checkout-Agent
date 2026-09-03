"""
Test Suite for Payment Architecture & Delegated Authorization (Bounded Autonomy)
"""
import pytest
from backend.infrastructure.payment_wallet_sandbox import PaymentWalletSandbox, SandboxChargeRequest
from backend.trust_safety.delegated_auth_policy import (
    DelegatedAuthPolicyEngine, DelegatedAuthEvaluationRequest, PolicyDecisionAction
)

def test_zero_raw_card_storage():
    wallet = PaymentWalletSandbox.get_wallet_instruments()
    assert len(wallet) >= 2
    for instrument in wallet:
        # Verify no 16-digit card PAN is stored
        assert " " not in instrument.token_handle or len(instrument.token_handle) != 19
        assert not instrument.token_handle.isdigit()
        assert instrument.token_handle.startswith("TKN_")

def test_scenario_groceries_auto_approved():
    # Buy detergent for ₹850
    req = DelegatedAuthEvaluationRequest(
        item_title="Surf Excel Matic Liquid Detergent 2L",
        category="groceries",
        price_inr=850.0,
        merchant_id="merchant-c",
        merchant_name="OmniStore Online",
        is_trusted_merchant=True,
        user_confirmed=False
    )
    decision = DelegatedAuthPolicyEngine.evaluate_transaction(req)

    assert decision.action == PolicyDecisionAction.AUTO_APPROVE
    assert decision.is_within_policy is True
    assert decision.is_merchant_trusted is True
    assert decision.is_product_allowed is True
    assert decision.delegated_token is not None
    assert decision.delegated_token.token_id.startswith("AUTH_MANDATE_")
    assert decision.delegated_token.max_authorized_amount == 850.0

def test_scenario_electronics_under_10k_auto_approved():
    # Buy Logitech MX Master 3S Mouse for ₹8,995
    req = DelegatedAuthEvaluationRequest(
        item_title="Logitech MX Master 3S Wireless Mouse",
        category="electronics",
        price_inr=8995.0,
        merchant_id="merchant-b",
        merchant_name="ElectroBazaar",
        is_trusted_merchant=True,
        user_confirmed=False
    )
    decision = DelegatedAuthPolicyEngine.evaluate_transaction(req)

    assert decision.action == PolicyDecisionAction.AUTO_APPROVE
    assert decision.requires_human_approval is False
    assert decision.delegated_token is not None

def test_scenario_electronics_above_10k_requires_user_auth():
    # Buy smartphone for ₹18,999
    req = DelegatedAuthEvaluationRequest(
        item_title="OnePlus Nord CE4 5G",
        category="electronics",
        price_inr=18999.0,
        merchant_id="merchant-b",
        merchant_name="ElectroBazaar",
        is_trusted_merchant=True,
        user_confirmed=False
    )
    decision = DelegatedAuthPolicyEngine.evaluate_transaction(req)

    assert decision.action == PolicyDecisionAction.ASK_USER
    assert decision.requires_human_approval is True
    assert decision.delegated_token is None

def test_scenario_laptop_109k_requires_auth_then_succeeds_on_confirmation():
    # 1. Unconfirmed request -> ASK USER
    req_unconfirmed = DelegatedAuthEvaluationRequest(
        item_title="ASUS ROG Strix G16 RTX 4070 Laptop",
        category="laptop",
        price_inr=109999.0,
        merchant_id="merchant-a",
        merchant_name="TechHub India",
        is_trusted_merchant=True,
        user_confirmed=False
    )
    decision1 = DelegatedAuthPolicyEngine.evaluate_transaction(req_unconfirmed)
    assert decision1.action == PolicyDecisionAction.ASK_USER
    assert decision1.requires_human_approval is True

    # 2. User confirms purchase with PIN -> AUTO APPROVE with Delegated Token
    req_confirmed = DelegatedAuthEvaluationRequest(
        item_title="ASUS ROG Strix G16 RTX 4070 Laptop",
        category="laptop",
        price_inr=109999.0,
        merchant_id="merchant-a",
        merchant_name="TechHub India",
        is_trusted_merchant=True,
        user_confirmed=True,
        auth_pin="9912"
    )
    decision2 = DelegatedAuthPolicyEngine.evaluate_transaction(req_confirmed)
    assert decision2.action == PolicyDecisionAction.AUTO_APPROVE
    assert decision2.delegated_token is not None
    assert decision2.delegated_token.max_authorized_amount == 109999.0

def test_hard_ceiling_blocked():
    # Transaction exceeding hard limit of ₹150,000
    req = DelegatedAuthEvaluationRequest(
        item_title="Apple Mac Studio M2 Ultra 128GB",
        category="electronics",
        price_inr=399000.0,
        merchant_id="merchant-a",
        merchant_name="TechHub India",
        is_trusted_merchant=True,
        user_confirmed=False
    )
    decision = DelegatedAuthPolicyEngine.evaluate_transaction(req)
    assert decision.action == PolicyDecisionAction.BLOCK
    assert "🛑 BLOCKED" in decision.decision_summary

def test_sandbox_charge_execution():
    # Execute payment using delegated token
    token = PaymentWalletSandbox.issue_delegated_auth_token("merchant-c", 850.0)
    charge_req = SandboxChargeRequest(
        merchant_id="merchant-c",
        amount=850.0,
        item_title="Surf Excel Matic 2L",
        category="groceries",
        delegated_token_id=token.token_id,
        payment_method_id="pm_upi_primary",
        user_confirmed=True
    )
    receipt = PaymentWalletSandbox.execute_sandbox_charge(charge_req)

    assert receipt.status == "SETTLED"
    assert receipt.amount == 850.0
    assert receipt.transaction_id.startswith("TXN_SANDBOX_")
    assert len(receipt.audit_hash) == 64
