"""
Phase 4 — Step 5: Checkout Security & Idempotency Service
Provides cryptographic request fingerprinting, durable PostgreSQL idempotency enforcement,
horizontal access boundary verification, quote/cart/merchant resource bindings, and anti-replay protection.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from backend.database.models import CheckoutIdempotencyRecordModel, CheckoutSessionModel, CartModel
from backend.core.errors import AgentCartException

logger = logging.getLogger("agentcart.checkout.security")

DEFAULT_IDEMPOTENCY_TTL_HOURS = 24


def normalize_for_fingerprint(data: Any) -> Any:
    """Recursively normalizes Python objects into deterministic JSON-serializable structures."""
    if isinstance(data, dict):
        # Exclude ephemeral tokens or metadata that do not affect business logic
        return {
            k: normalize_for_fingerprint(v)
            for k, v in sorted(data.items())
            if k not in {"idempotency_key", "request_id", "correlation_id", "client_timestamp"}
        }
    elif isinstance(data, (list, tuple)):
        return [normalize_for_fingerprint(item) for item in data]
    elif isinstance(data, Decimal):
        return f"{data:.2f}"
    elif isinstance(data, datetime):
        return data.isoformat()
    elif hasattr(data, "model_dump"):
        return normalize_for_fingerprint(data.model_dump())
    elif hasattr(data, "dict"):
        return normalize_for_fingerprint(data.dict())
    return data


class CheckoutSecurityService:
    """
    Coordinates server-authoritative idempotency, session authorization, and resource binding rules.
    """

    @classmethod
    def compute_request_hash(cls, payload: Any) -> str:
        """Computes deterministic SHA-256 fingerprint of normalized request body."""
        normalized = normalize_for_fingerprint(payload)
        serialized = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    @classmethod
    def check_idempotency(
        cls,
        db: Session,
        idempotency_key: str,
        operation: str,
        payload: Any,
        session_id: Optional[str] = None
    ) -> Tuple[Optional[CheckoutIdempotencyRecordModel], bool]:
        """
        Queries durable PostgreSQL storage for existing idempotency records.
        Returns:
            (record, is_cache_hit): If cache hit, record contains cached response.
        Raises:
            IDEMPOTENCY_CONFLICT (409) if key is reused with a different request payload.
            UNAUTHORIZED_CHECKOUT_ACCESS (403) if key belongs to another user session.
            CONCURRENT_MODIFICATION (409) if request with this key is currently in PROCESSING state.
        """
        clean_key = idempotency_key.strip()
        record = db.query(CheckoutIdempotencyRecordModel).filter(
            CheckoutIdempotencyRecordModel.idempotency_key == clean_key,
            CheckoutIdempotencyRecordModel.operation == operation
        ).first()

        if not record:
            return None, False

        now = datetime.now(timezone.utc)
        # Check expiration
        if record.expires_at and now > record.expires_at:
            db.delete(record)
            db.commit()
            return None, False

        # Compute current request fingerprint
        current_hash = cls.compute_request_hash(payload)

        # 1. Reject key reuse with mismatched request payload
        if record.request_hash != current_hash:
            logger.warning(
                "Idempotency conflict detected for key '%s' on operation '%s'. Stored hash: %s, Current hash: %s",
                clean_key, operation, record.request_hash, current_hash
            )
            raise AgentCartException(
                f"Idempotency key '{clean_key}' was previously used with a different request payload for operation '{operation}'.",
                code="IDEMPOTENCY_CONFLICT",
                status_code=409,
                details={
                    "idempotency_key": clean_key,
                    "operation": operation
                }
            )

        # 2. Horizontal session access check
        if session_id and record.session_id and record.session_id != session_id:
            logger.warning(
                "Unauthorized horizontal access attempt to idempotency key '%s' by session '%s' (owner: '%s')",
                clean_key, session_id, record.session_id
            )
            raise AgentCartException(
                "Idempotency key was created by a different user session.",
                code="UNAUTHORIZED_CHECKOUT_ACCESS",
                status_code=403
            )

        # 3. Check status
        if record.status == "PROCESSING":
            raise AgentCartException(
                f"A request with idempotency key '{clean_key}' is currently being processed. Please retry shortly.",
                code="CONCURRENT_MODIFICATION",
                status_code=409
            )

        logger.info(
            "Idempotent replay detected for key '%s' on operation '%s'. Returning cached response.",
            clean_key, operation
        )
        return record, True

    @classmethod
    def record_idempotency_success(
        cls,
        db: Session,
        idempotency_key: str,
        operation: str,
        resource_id: Optional[str],
        session_id: Optional[str],
        payload: Any,
        response_body: Any,
        response_code: int = 200,
        ttl_hours: int = DEFAULT_IDEMPOTENCY_TTL_HOURS
    ) -> CheckoutIdempotencyRecordModel:
        """
        Durable persistence of successful operation response in PostgreSQL.
        """
        clean_key = idempotency_key.strip()
        request_hash = cls.compute_request_hash(payload)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=ttl_hours)

        # Serialize response body
        if hasattr(response_body, "model_dump"):
            serialized_body = json.loads(json.dumps(response_body.model_dump(), default=str))
        elif hasattr(response_body, "dict"):
            serialized_body = json.loads(json.dumps(response_body.dict(), default=str))
        elif isinstance(response_body, dict):
            serialized_body = json.loads(json.dumps(response_body, default=str))
        else:
            serialized_body = str(response_body)

        existing = db.query(CheckoutIdempotencyRecordModel).filter(
            CheckoutIdempotencyRecordModel.idempotency_key == clean_key,
            CheckoutIdempotencyRecordModel.operation == operation
        ).first()

        if existing:
            existing.status = "COMPLETED"
            existing.response_code = response_code
            existing.response_body = serialized_body
            existing.resource_id = resource_id
            existing.session_id = session_id or existing.session_id
            existing.expires_at = expires_at
            db.commit()
            return existing

        record = CheckoutIdempotencyRecordModel(
            idempotency_key=clean_key,
            operation=operation,
            resource_id=resource_id,
            session_id=session_id,
            request_hash=request_hash,
            status="COMPLETED",
            response_code=response_code,
            response_body=serialized_body,
            created_at=now,
            expires_at=expires_at
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def validate_horizontal_access(
        cls,
        session: CheckoutSessionModel,
        caller_session_id: Optional[str]
    ) -> None:
        """
        Enforces horizontal tenant/user access control: caller cannot mutate or view a checkout session
        belonging to a different user session.
        """
        if caller_session_id and session.session_id:
            if session.session_id != caller_session_id:
                logger.warning(
                    "Horizontal access violation: Session '%s' attempted to access checkout session '%s' owned by '%s'",
                    caller_session_id, session.id, session.session_id
                )
                raise AgentCartException(
                    "Access denied: Checkout session belongs to another user session.",
                    code="UNAUTHORIZED_CHECKOUT_ACCESS",
                    status_code=403,
                    details={"checkout_session_id": session.id}
                )

    @classmethod
    def validate_cart_ownership(
        cls,
        cart: CartModel,
        caller_session_id: Optional[str]
    ) -> None:
        """
        Enforces horizontal tenant/user access control on shopping cart.
        """
        if caller_session_id and cart.session_id:
            if cart.session_id != caller_session_id:
                logger.warning(
                    "Horizontal cart access violation: Session '%s' attempted to access cart '%s' owned by '%s'",
                    caller_session_id, cart.id, cart.session_id
                )
                raise AgentCartException(
                    "Access denied: Cart belongs to another user session.",
                    code="UNAUTHORIZED_CART_ACCESS",
                    status_code=403,
                    details={"cart_id": cart.id}
                )

    @classmethod
    def validate_quote_bindings(
        cls,
        session: CheckoutSessionModel,
        quote_id: Optional[str] = None,
        cart_id: Optional[str] = None,
        merchant_code: Optional[str] = None
    ) -> None:
        """
        Enforces strict cryptographic / relational resource binding on checkout sessions.
        Prevents switching quotes, carts, or merchants mid-checkout.
        """
        if quote_id and session.id != quote_id:
            raise AgentCartException(
                f"Checkout quote binding mismatch: Specified quote_id '{quote_id}' does not match session '{session.id}'.",
                code="QUOTE_MISMATCH",
                status_code=400,
                details={"session_quote_id": session.id, "requested_quote_id": quote_id}
            )

        if cart_id and session.cart_id != cart_id:
            raise AgentCartException(
                f"Checkout cart binding mismatch: Session is bound to cart '{session.cart_id}', not '{cart_id}'.",
                code="CART_MISMATCH",
                status_code=400,
                details={"session_cart_id": session.cart_id, "requested_cart_id": cart_id}
            )

        if merchant_code:
            expected_merchant = getattr(session.merchant, "merchant_code", None) if getattr(session, "merchant", None) else None
            if expected_merchant and expected_merchant != merchant_code:
                raise AgentCartException(
                    f"Checkout merchant binding mismatch: Session is bound to merchant '{expected_merchant}', not '{merchant_code}'.",
                    code="MERCHANT_MISMATCH",
                    status_code=400,
                    details={"session_merchant": expected_merchant, "requested_merchant": merchant_code}
                )
