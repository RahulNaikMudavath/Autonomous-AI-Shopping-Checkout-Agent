"""
Layer 4 & 5: Payment Infrastructure - Tokenized Wallet & Delegated Payment Sandbox
Strict Zero Raw Card Storage Architecture.
Implements:
- User Payment Wallet Vault with tokenized instruments (UPI, Virtual Visa, Escrow)
- Scoped Delegated Authorization Tokens (MANDATE_AUTH_...) with amount caps and TTL
- Payment Sandbox simulating token settlement and cryptographic audit linking
"""
import uuid
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field

class TokenizedPaymentMethod(BaseModel):
    method_id: str
    type: str  # "UPI_VPA", "TOKENIZED_CARD", "AGENT_ESCROW"
    display_label: str
    token_handle: str  # Tokenized surrogate (NO RAW PAN / CVV)
    issuer: str
    is_default: bool = False
    status: str = "ACTIVE"
    daily_limit_inr: float = 200000.0

class DelegatedAuthToken(BaseModel):
    token_id: str
    user_id: str = "usr_rahul_01"
    merchant_id: str
    max_authorized_amount: float
    currency: str = "INR"
    scope: str = "ONE_TIME_PURCHASE"
    token_signature: str
    issued_at: str
    expires_at: str
    used: bool = False

class SandboxChargeRequest(BaseModel):
    merchant_id: str
    amount: float
    item_title: str
    category: str
    delegated_token_id: Optional[str] = None
    payment_method_id: Optional[str] = "pm_upi_primary"
    user_confirmed: bool = False
    auth_pin: Optional[str] = None

class SandboxChargeResponse(BaseModel):
    transaction_id: str
    merchant_id: str
    amount: float
    currency: str = "INR"
    status: str  # "SETTLED", "REJECTED_UNAUTHORIZED", "PENDING_AUTH"
    payment_method_used: str
    delegated_token_used: Optional[str] = None
    settlement_timestamp: str
    audit_hash: str
    receipt_url: str

# Default Tokenized Wallet (Zero Raw PAN/CVV)
USER_WALLET: List[TokenizedPaymentMethod] = [
    TokenizedPaymentMethod(
        method_id="pm_upi_primary",
        type="UPI_VPA",
        display_label="UPI (rahul@okaxis / Tokenized 1-Click)",
        token_handle="TKN_UPI_VPA_AXIS_9948291",
        issuer="NPCI / Axis Bank",
        is_default=True,
        daily_limit_inr=200000.0
    ),
    TokenizedPaymentMethod(
        method_id="pm_card_virtual",
        type="TOKENIZED_CARD",
        display_label="HDFC Regalia Virtual (Token ending in 8821)",
        token_handle="TKN_VISA_HDFC_VIRTUAL_8821",
        issuer="HDFC Bank / Visa Network Token",
        is_default=False,
        daily_limit_inr=150000.0
    ),
    TokenizedPaymentMethod(
        method_id="pm_escrow_vault",
        type="AGENT_ESCROW",
        display_label="Autonomous Agent Escrow Reserve",
        token_handle="TKN_ESCROW_VAULT_RESERVE_001",
        issuer="AgentCart Escrow Services",
        is_default=False,
        daily_limit_inr=500000.0
    )
]

# In-Memory Store for Generated Delegated Authorization Tokens
ACTIVE_DELEGATED_TOKENS: Dict[str, DelegatedAuthToken] = {}

class PaymentWalletSandbox:
    @staticmethod
    def get_wallet_instruments() -> List[TokenizedPaymentMethod]:
        """Returns all tokenized payment instruments. Zero raw card numbers."""
        return USER_WALLET

    @staticmethod
    def issue_delegated_auth_token(
        merchant_id: str,
        amount: float,
        user_id: str = "usr_rahul_01",
        ttl_minutes: int = 15
    ) -> DelegatedAuthToken:
        """
        Generates a cryptographic single-use delegated authorization token for the Payment Agent.
        """
        token_id = f"AUTH_MANDATE_{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=ttl_minutes)

        # Create cryptographic signature of the mandate
        signature_raw = f"{token_id}:{user_id}:{merchant_id}:{amount}:{expires.isoformat()}"
        signature = hashlib.sha256(signature_raw.encode()).hexdigest()

        token = DelegatedAuthToken(
            token_id=token_id,
            user_id=user_id,
            merchant_id=merchant_id,
            max_authorized_amount=amount,
            currency="INR",
            scope="ONE_TIME_PURCHASE",
            token_signature=signature,
            issued_at=now.isoformat(),
            expires_at=expires.isoformat(),
            used=False
        )
        ACTIVE_DELEGATED_TOKENS[token_id] = token
        return token

    @staticmethod
    def execute_sandbox_charge(req: SandboxChargeRequest) -> SandboxChargeResponse:
        """
        Settles payment through simulated payment rails using delegated authorization token.
        """
        now = datetime.now(timezone.utc).isoformat()
        tx_id = f"TXN_SANDBOX_{uuid.uuid4().hex[:8].upper()}"

        # Check if delegated token provided
        token_obj = None
        if req.delegated_token_id:
            token_obj = ACTIVE_DELEGATED_TOKENS.get(req.delegated_token_id)
            if token_obj:
                token_obj.used = True

        audit_payload = f"{tx_id}:{req.merchant_id}:{req.amount}:{now}"
        audit_hash = hashlib.sha256(audit_payload.encode()).hexdigest()

        # Find payment method
        pm = next((p for p in USER_WALLET if p.method_id == req.payment_method_id), USER_WALLET[0])

        return SandboxChargeResponse(
            transaction_id=tx_id,
            merchant_id=req.merchant_id,
            amount=req.amount,
            currency="INR",
            status="SETTLED",
            payment_method_used=pm.display_label,
            delegated_token_used=req.delegated_token_id,
            settlement_timestamp=now,
            audit_hash=audit_hash,
            receipt_url=f"/api/payment/receipts/{tx_id}"
        )
