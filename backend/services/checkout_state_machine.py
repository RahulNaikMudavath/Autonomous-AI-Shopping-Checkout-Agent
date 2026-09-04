"""
Phase 4 — Step 4: Checkout State Machine Service
Enforces deterministic, server-authoritative state transitions across the checkout lifecycle.
Guarantees terminal state immutability, live pre-transition revalidation, concurrency safety, and idempotency.
"""
from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from backend.database.models import (
    CheckoutSessionModel, CartModel, ProductModel, MerchantModel, ShippingOptionModel
)
from backend.domain.marketplace import (
    CheckoutSessionStatus, CheckoutTransitionAction, CheckoutTransitionRequest,
    CheckoutTransitionResponse, CheckoutSummaryResponse, StateTransitionAuditLog
)
from backend.services.inventory_service import InventoryService, OutOfStockException, InsufficientInventoryException
from backend.services.pricing_service import quantize_money, ZERO
from backend.services.checkout_security_service import CheckoutSecurityService
from backend.core.errors import AgentCartException, EntityNotFoundException

logger = logging.getLogger("agentcart.checkout.statemachine")


class InvalidStateTransitionException(AgentCartException):
    """Raised when an action or state transition violates the deterministic checkout state machine."""
    def __init__(
        self,
        current_state: str,
        requested_action: str,
        target_state: Optional[str] = None,
        message: Optional[str] = None
    ):
        msg = message or f"Invalid transition: Action '{requested_action}' is not permitted from state '{current_state}'."
        super().__init__(
            message=msg,
            code="INVALID_STATE_TRANSITION",
            status_code=400,
            details={
                "current_state": current_state,
                "requested_action": requested_action,
                "target_state": target_state
            }
        )


class CheckoutStateMachine:
    """
    Server-authoritative state machine governing the checkout lifecycle.
    """

    TERMINAL_STATES: Set[str] = {
        CheckoutSessionStatus.COMPLETED.value,
        CheckoutSessionStatus.CANCELLED.value,
        CheckoutSessionStatus.EXPIRED.value,
        CheckoutSessionStatus.FAILED.value,
        CheckoutSessionStatus.INVALID.value,
    }

    # Deterministic mapping: current_state -> { action: target_state }
    TRANSITION_TABLE: Dict[str, Dict[str, str]] = {
        CheckoutSessionStatus.QUOTE_CREATED.value: {
            CheckoutTransitionAction.VALIDATE_QUOTE.value: CheckoutSessionStatus.QUOTE_VALID.value,
            CheckoutTransitionAction.REQUEST_AUTHORIZATION.value: CheckoutSessionStatus.AUTHORIZATION_REQUIRED.value,
            CheckoutTransitionAction.CANCEL.value: CheckoutSessionStatus.CANCELLED.value,
            CheckoutTransitionAction.INVALIDATE.value: CheckoutSessionStatus.INVALID.value,
            CheckoutTransitionAction.FAIL.value: CheckoutSessionStatus.FAILED.value,
        },
        CheckoutSessionStatus.PENDING.value: {  # Alias for QUOTE_CREATED
            CheckoutTransitionAction.VALIDATE_QUOTE.value: CheckoutSessionStatus.QUOTE_VALID.value,
            CheckoutTransitionAction.REQUEST_AUTHORIZATION.value: CheckoutSessionStatus.AUTHORIZATION_REQUIRED.value,
            CheckoutTransitionAction.CANCEL.value: CheckoutSessionStatus.CANCELLED.value,
            CheckoutTransitionAction.INVALIDATE.value: CheckoutSessionStatus.INVALID.value,
            CheckoutTransitionAction.FAIL.value: CheckoutSessionStatus.FAILED.value,
        },
        CheckoutSessionStatus.QUOTE_VALID.value: {
            CheckoutTransitionAction.REQUEST_AUTHORIZATION.value: CheckoutSessionStatus.AUTHORIZATION_REQUIRED.value,
            CheckoutTransitionAction.VALIDATE_QUOTE.value: CheckoutSessionStatus.QUOTE_VALID.value,
            CheckoutTransitionAction.CANCEL.value: CheckoutSessionStatus.CANCELLED.value,
            CheckoutTransitionAction.INVALIDATE.value: CheckoutSessionStatus.INVALID.value,
            CheckoutTransitionAction.FAIL.value: CheckoutSessionStatus.FAILED.value,
        },
        CheckoutSessionStatus.AUTHORIZATION_REQUIRED.value: {
            CheckoutTransitionAction.AUTHORIZE.value: CheckoutSessionStatus.AUTHORIZED.value,
            CheckoutTransitionAction.CANCEL.value: CheckoutSessionStatus.CANCELLED.value,
            CheckoutTransitionAction.INVALIDATE.value: CheckoutSessionStatus.INVALID.value,
            CheckoutTransitionAction.FAIL.value: CheckoutSessionStatus.FAILED.value,
        },
        CheckoutSessionStatus.AUTHORIZED.value: {
            CheckoutTransitionAction.INITIATE_PAYMENT.value: CheckoutSessionStatus.PAYMENT_PENDING.value,
            CheckoutTransitionAction.CANCEL.value: CheckoutSessionStatus.CANCELLED.value,
            CheckoutTransitionAction.INVALIDATE.value: CheckoutSessionStatus.INVALID.value,
            CheckoutTransitionAction.FAIL.value: CheckoutSessionStatus.FAILED.value,
        },
        CheckoutSessionStatus.PAYMENT_PENDING.value: {
            CheckoutTransitionAction.CONFIRM_PAYMENT.value: CheckoutSessionStatus.PAID.value,
            CheckoutTransitionAction.CANCEL.value: CheckoutSessionStatus.CANCELLED.value,
            CheckoutTransitionAction.FAIL.value: CheckoutSessionStatus.FAILED.value,
        },
        CheckoutSessionStatus.PAID.value: {
            CheckoutTransitionAction.SUBMIT_ORDER.value: CheckoutSessionStatus.ORDER_PENDING.value,
            CheckoutTransitionAction.FAIL.value: CheckoutSessionStatus.FAILED.value,
        },
        CheckoutSessionStatus.ORDER_PENDING.value: {
            CheckoutTransitionAction.COMPLETE.value: CheckoutSessionStatus.COMPLETED.value,
            CheckoutTransitionAction.FAIL.value: CheckoutSessionStatus.FAILED.value,
        },
        # Terminal states have no permitted outgoing transitions
        CheckoutSessionStatus.COMPLETED.value: {},
        CheckoutSessionStatus.CANCELLED.value: {},
        CheckoutSessionStatus.EXPIRED.value: {},
        CheckoutSessionStatus.FAILED.value: {},
        CheckoutSessionStatus.INVALID.value: {},
    }

    @classmethod
    def get_allowed_actions(cls, current_state: str) -> List[str]:
        """Returns the list of actions permitted from the specified state."""
        return list(cls.TRANSITION_TABLE.get(current_state, {}).keys())

    @classmethod
    def transition(
        cls,
        db: Session,
        checkout_session_id: str,
        request: CheckoutTransitionRequest,
        idempotency_key: Optional[str] = None,
        caller_session_id: Optional[str] = None
    ) -> CheckoutTransitionResponse:
        """
        Executes a deterministic state transition on the checkout session.
        Validates state machine rules, horizontal access, resource bindings, runs live precondition revalidation,
        handles concurrency via row-level locks, ensures idempotency, and records audit telemetry.
        """
        action_val = request.action.value if hasattr(request.action, "value") else str(request.action)

        # 1. Row-level lock on the checkout session to prevent concurrent race conditions
        session = db.query(CheckoutSessionModel).filter(
            CheckoutSessionModel.id == checkout_session_id
        ).with_for_update().first()

        if not session:
            raise EntityNotFoundException("CheckoutSession", checkout_session_id)

        # 2. Horizontal Access Control & Session Ownership Verification
        CheckoutSecurityService.validate_horizontal_access(session, caller_session_id)

        # 3. Cryptographic & Resource Binding Verification (Quote, Cart, Merchant)
        CheckoutSecurityService.validate_quote_bindings(
            session=session,
            quote_id=request.quote_id,
            cart_id=request.cart_id,
            merchant_code=request.merchant_code
        )

        effective_session_id = caller_session_id or session.session_id

        # 4. Durable PostgreSQL Idempotency Gate
        if idempotency_key:
            record, is_hit = CheckoutSecurityService.check_idempotency(
                db=db,
                idempotency_key=idempotency_key,
                operation=f"checkout_transition:{action_val}",
                payload=request,
                session_id=effective_session_id
            )
            if is_hit and record and record.response_body:
                return CheckoutTransitionResponse(**record.response_body)

        current_state = session.status
        now = datetime.now(timezone.utc)

        # 5. Check for quote expiration first if session is in an active state
        if current_state not in cls.TERMINAL_STATES:
            if session.expires_at and now > session.expires_at:
                session.status = CheckoutSessionStatus.EXPIRED.value
                db.commit()
                raise AgentCartException(
                    "Checkout quote has expired (TTL exceeded). Please generate a new quote.",
                    code="QUOTE_EXPIRED",
                    status_code=400,
                    details={"checkout_session_id": session.id, "expires_at": session.expires_at.isoformat()}
                )

        # 6. Check allowed actions from current state
        allowed_actions = cls.TRANSITION_TABLE.get(current_state, {})
        if action_val not in allowed_actions:
            if current_state in cls.TERMINAL_STATES:
                raise InvalidStateTransitionException(
                    current_state=current_state,
                    requested_action=action_val,
                    message=f"Cannot transition checkout session from terminal state '{current_state}'."
                )
            raise InvalidStateTransitionException(
                current_state=current_state,
                requested_action=action_val,
                message=f"Action '{action_val}' is not permitted from state '{current_state}'. Allowed actions: {list(allowed_actions.keys())}"
            )

        target_state = allowed_actions[action_val]

        # 7. Idempotency Check: if session is already in target_state, return gracefully without double side-effects
        if current_state == target_state:
            logger.info("Idempotent transition request for session %s: already in %s", session.id, target_state)
            summary = cls._build_summary(db, session)
            resp = CheckoutTransitionResponse(
                success=True,
                message=f"Checkout session is already in state '{target_state}' (idempotent request).",
                checkout_session_id=session.id,
                previous_state=current_state,
                current_state=CheckoutSessionStatus(target_state),
                action=request.action,
                checkout=summary,
                audit_log=StateTransitionAuditLog(
                    previous_state=current_state,
                    target_state=target_state,
                    action=action_val,
                    timestamp=now.isoformat(),
                    reason=request.reason or "Idempotent transition",
                    success=True
                )
            )
            if idempotency_key:
                CheckoutSecurityService.record_idempotency_success(
                    db=db,
                    idempotency_key=idempotency_key,
                    operation=f"checkout_transition:{action_val}",
                    resource_id=session.id,
                    session_id=effective_session_id,
                    payload=request,
                    response_body=resp,
                    response_code=200
                )
            return resp

        # 8. Pre-Transition Live Invariant Revalidation (for forward progression actions)
        if action_val in {
            CheckoutTransitionAction.VALIDATE_QUOTE.value,
            CheckoutTransitionAction.REQUEST_AUTHORIZATION.value,
            CheckoutTransitionAction.AUTHORIZE.value,
            CheckoutTransitionAction.INITIATE_PAYMENT.value,
            CheckoutTransitionAction.CONFIRM_PAYMENT.value,
            CheckoutTransitionAction.SUBMIT_ORDER.value
        }:
            cls._validate_preconditions(db, session)

        # 9. Apply State Transition & Monotonically Increment Version
        session.status = target_state
        session.version = (session.version or 1) + 1
        session.updated_at = now

        db.commit()
        db.refresh(session)

        logger.info(
            "Executed checkout state transition: session=%s, action=%s, %s -> %s (version=%s)",
            session.id, action_val, current_state, target_state, session.version
        )

        summary = cls._build_summary(db, session)

        audit_log = StateTransitionAuditLog(
            previous_state=current_state,
            target_state=target_state,
            action=action_val,
            timestamp=now.isoformat(),
            reason=request.reason,
            success=True
        )

        transition_response = CheckoutTransitionResponse(
            success=True,
            message=f"Checkout session successfully transitioned from '{current_state}' to '{target_state}'.",
            checkout_session_id=session.id,
            previous_state=current_state,
            current_state=CheckoutSessionStatus(target_state),
            action=request.action,
            checkout=summary,
            audit_log=audit_log
        )

        # 10. Persist Durable Idempotency Record
        if idempotency_key:
            CheckoutSecurityService.record_idempotency_success(
                db=db,
                idempotency_key=idempotency_key,
                operation=f"checkout_transition:{action_val}",
                resource_id=session.id,
                session_id=effective_session_id,
                payload=request,
                response_body=transition_response,
                response_code=200
            )

        return transition_response

    @classmethod
    def _validate_preconditions(cls, db: Session, session: CheckoutSessionModel) -> None:
        """
        Executes strict live revalidation of cart staleness, merchant, products, inventory, prices, and shipping.
        If any invariant is breached, marks session as INVALID and rejects the transition with structured error.
        """
        # A. Cart Verification
        cart = db.query(CartModel).filter(CartModel.id == session.cart_id).first()
        if not cart:
            session.status = CheckoutSessionStatus.INVALID.value
            db.commit()
            raise EntityNotFoundException("Cart", session.cart_id)

        if cart.status != "ACTIVE":
            session.status = CheckoutSessionStatus.INVALID.value
            db.commit()
            raise AgentCartException(
                f"Cart '{cart.id}' is not active (status={cart.status}).",
                code="CART_INACTIVE",
                status_code=400
            )

        # B. Cart Staleness Detection: Cart updated after quote creation
        if cart.updated_at and session.created_at and cart.updated_at > session.created_at:
            session.status = CheckoutSessionStatus.INVALID.value
            db.commit()
            raise AgentCartException(
                "The shopping cart was modified after this quote was created. Please refresh and generate a new quote.",
                code="QUOTE_STALE",
                status_code=400,
                details={"cart_id": cart.id, "cart_updated_at": cart.updated_at.isoformat(), "quote_created_at": session.created_at.isoformat()}
            )

        # C. Merchant Verification
        merchant = db.query(MerchantModel).filter(MerchantModel.id == session.merchant_id).first()
        if not merchant or not merchant.is_active:
            session.status = CheckoutSessionStatus.INVALID.value
            db.commit()
            raise AgentCartException(
                f"Merchant '{session.merchant_id}' is currently inactive.",
                code="MERCHANT_INACTIVE",
                status_code=400
            )

        # D. Product, Price & Inventory Revalidation
        snapshot_items = session.items_snapshot or []
        if not snapshot_items:
            session.status = CheckoutSessionStatus.INVALID.value
            db.commit()
            raise AgentCartException("Checkout session contains no items.", code="EMPTY_CART", status_code=400)

        for item in snapshot_items:
            product_id = item.get("product_id")
            quantity = int(item.get("quantity", 1))
            snapshot_unit_price = quantize_money(item.get("unit_price", "0.00"))

            product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
            if not product:
                session.status = CheckoutSessionStatus.INVALID.value
                db.commit()
                raise EntityNotFoundException("Product", product_id)

            if not product.is_active:
                session.status = CheckoutSessionStatus.INVALID.value
                db.commit()
                raise AgentCartException(
                    f"Product '{product.title}' is no longer active for sale.",
                    code="PRODUCT_INACTIVE",
                    status_code=400,
                    details={"product_id": product.id}
                )

            # Live Catalog Price check
            live_price = quantize_money(product.current_price)
            if live_price != snapshot_unit_price:
                session.status = CheckoutSessionStatus.INVALID.value
                db.commit()
                raise AgentCartException(
                    f"Price for '{product.title}' has changed from ₹{snapshot_unit_price:,.2f} to ₹{live_price:,.2f}.",
                    code="PRICE_CHANGED",
                    status_code=400,
                    details={
                        "product_id": product.id,
                        "old_price": str(snapshot_unit_price),
                        "new_price": str(live_price)
                    }
                )

            # Live Stock Check
            can_fulfill, avail_qty, _ = InventoryService.check_availability(db, product.id, quantity)
            if not can_fulfill:
                session.status = CheckoutSessionStatus.INVALID.value
                db.commit()
                if avail_qty == 0:
                    raise OutOfStockException(product.id, message=f"Item '{product.title}' is currently out of stock.")
                raise InsufficientInventoryException(product.id, quantity, avail_qty)

        # E. Shipping Option Verification
        if session.shipping_option_id:
            shipping_opt = db.query(ShippingOptionModel).filter(
                ShippingOptionModel.id == session.shipping_option_id
            ).first()
            if not shipping_opt or not shipping_opt.is_active or shipping_opt.merchant_id != session.merchant_id:
                session.status = CheckoutSessionStatus.INVALID.value
                db.commit()
                raise AgentCartException(
                    "The selected shipping option is no longer valid or does not belong to the merchant.",
                    code="SHIPPING_INVALID",
                    status_code=400
                )

    @classmethod
    def _build_summary(cls, db: Session, session: CheckoutSessionModel) -> CheckoutSummaryResponse:
        """Constructs CheckoutSummaryResponse from current session record."""
        merchant = db.query(MerchantModel).filter(MerchantModel.id == session.merchant_id).first()
        from backend.services.checkout_service import CheckoutService
        return CheckoutService.get_checkout_session(db, session.id)
