"""
Phase 2: Checkout Preparation & Pre-Purchase Validation Service
Performs authoritative re-validation of inventory, pricing, promotions, and shipping before order placement.
Creates server-signed CheckoutSession records.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session, joinedload

from backend.database.models import (
    CartModel, CartItemModel, CheckoutSessionModel, ProductModel,
    MerchantModel, ShippingOptionModel, DiscountModel
)
from backend.domain.marketplace import (
    CheckoutPrepareRequest, CheckoutSummaryResponse, CheckoutItemSummary,
    ShippingOptionDetail, CheckoutSessionStatus
)
from backend.services.pricing_service import PricingService, quantize_money, ZERO
from backend.services.inventory_service import InventoryService, OutOfStockException, InsufficientInventoryException
from backend.services.shipping_service import ShippingService
from backend.core.errors import AgentCartException, EntityNotFoundException

logger = logging.getLogger("agentcart.checkout")

CHECKOUT_EXPIRATION_MINUTES = 15


class CheckoutValidationException(AgentCartException):
    """Raised when cart or item invariants fail pre-checkout gates."""
    def __init__(self, message: str, code: str = "CHECKOUT_VALIDATION_FAILED", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=400,
            details=details or {}
        )


class CheckoutService:
    """
    Coordinates pre-order verification and checkout session preparation.
    """

    @classmethod
    def prepare_checkout(
        cls,
        db: Session,
        request: CheckoutPrepareRequest
    ) -> CheckoutSummaryResponse:
        """
        Executes the 8-step deterministic checkout preparation workflow:
        1. Retrieve cart & verify non-empty.
        2. Re-check live inventory availability for all items.
        3. Recalculate subtotal using authoritative product catalog prices.
        4. Authoritatively evaluate promo code discounts.
        5. Calculate server-side shipping cost.
        6. Compute applicable taxes and final total.
        7. Persist CheckoutSession with 15-minute TTL.
        8. Return validated CheckoutSummaryResponse.
        """
        # 1. Cart Verification
        cart = db.query(CartModel).options(
            joinedload(CartModel.merchant),
            joinedload(CartModel.items).joinedload(CartItemModel.product)
        ).filter(
            CartModel.id == request.cart_id,
            CartModel.status == "ACTIVE"
        ).first()

        if not cart:
            raise EntityNotFoundException("Cart", request.cart_id)

        if not cart.items:
            raise CheckoutValidationException("Cannot prepare checkout for an empty cart.", code="EMPTY_CART")

        merchant = cart.merchant
        items_snapshot = []
        item_tuples = []
        item_summaries = []

        # 2 & 3. Inventory & Price Revalidation
        for it in cart.items:
            prod = it.product or db.query(ProductModel).filter(ProductModel.id == it.product_id).first()
            if not prod or not prod.is_active:
                raise CheckoutValidationException(
                    f"Product '{it.product_id}' is no longer active in the catalog.",
                    code="PRODUCT_UNAVAILABLE",
                    details={"product_id": it.product_id}
                )

            # Check live inventory
            can_fulfill, avail_qty, state = InventoryService.check_availability(db, prod.id, it.quantity)
            if not can_fulfill:
                if avail_qty == 0:
                    raise OutOfStockException(prod.id, message=f"Item '{prod.title}' went out of stock during checkout.")
                raise InsufficientInventoryException(prod.id, it.quantity, avail_qty)

            current_u_price = quantize_money(prod.current_price)
            line_total = PricingService.calculate_line_item_total(current_u_price, it.quantity)

            item_tuples.append((current_u_price, it.quantity))
            items_snapshot.append({
                "product_id": prod.id,
                "product_title": prod.title,
                "sku": prod.sku,
                "quantity": it.quantity,
                "unit_price": str(current_u_price),
                "total_price": str(line_total)
            })
            item_summaries.append(CheckoutItemSummary(
                product_id=prod.id,
                product_title=prod.title,
                sku=prod.sku,
                quantity=it.quantity,
                unit_price=current_u_price,
                total_price=line_total
            ))

        subtotal = PricingService.calculate_subtotal(item_tuples)

        # 4. Authoritative Discount Evaluation
        discount_amount, discount_model = PricingService.evaluate_discount(
            db=db,
            merchant_id=merchant.id,
            promo_code=request.promo_code,
            subtotal=subtotal
        )

        # 5. Authoritative Shipping Evaluation
        shipping_cost = ShippingService.calculate_shipping_cost(
            db=db,
            merchant_id=merchant.id,
            shipping_option_id=request.shipping_option_id,
            subtotal=subtotal
        )

        # Selected Shipping Option Details
        selected_shipping_opt = None
        if request.shipping_option_id:
            opt = ShippingService.get_shipping_option_by_id(db, request.shipping_option_id)
            if opt:
                selected_shipping_opt = ShippingOptionDetail(
                    id=opt.id,
                    merchant_id=opt.merchant_id,
                    code=opt.code,
                    name=opt.name,
                    cost=quantize_money(opt.cost),
                    estimated_days=opt.estimated_days,
                    delivery_type=opt.delivery_type,
                    is_active=opt.is_active
                )

        # 6. Tax & Grand Total Computation
        tax_amount = PricingService.calculate_tax(subtotal - discount_amount)
        grand_total = PricingService.compute_grand_total(
            subtotal=subtotal,
            discount=discount_amount,
            shipping=shipping_cost,
            tax=tax_amount
        )

        # 7. Persist Checkout Session
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=CHECKOUT_EXPIRATION_MINUTES)

        checkout_session = CheckoutSessionModel(
            cart_id=cart.id,
            merchant_id=merchant.id,
            session_id=cart.session_id,
            subtotal=subtotal,
            discount_total=discount_amount,
            shipping_total=shipping_cost,
            tax_total=tax_amount,
            grand_total=grand_total,
            currency="INR",
            shipping_option_id=request.shipping_option_id,
            promo_code=request.promo_code if discount_model else None,
            items_snapshot=items_snapshot,
            status="PENDING",
            expires_at=expires_at,
            created_at=now
        )
        db.add(checkout_session)
        db.commit()
        db.refresh(checkout_session)

        logger.info(
            "Prepared CheckoutSession %s for merchant %s. Subtotal: ₹%s, Grand Total: ₹%s",
            checkout_session.id, merchant.merchant_code, subtotal, grand_total
        )

        return CheckoutSummaryResponse(
            checkout_session_id=checkout_session.id,
            cart_id=cart.id,
            merchant_code=merchant.merchant_code,
            merchant_name=merchant.display_name,
            subtotal=subtotal,
            discount_total=discount_amount,
            shipping_total=shipping_cost,
            tax_total=tax_amount,
            grand_total=grand_total,
            currency="INR",
            items=item_summaries,
            shipping_option=selected_shipping_opt,
            applied_promo=request.promo_code if discount_model else None,
            status=CheckoutSessionStatus.PENDING,
            expires_at=expires_at.isoformat(),
            created_at=now.isoformat()
        )

    @classmethod
    def get_checkout_session(cls, db: Session, session_id: str) -> Optional[CheckoutSessionModel]:
        """Retrieves checkout session by ID."""
        return db.query(CheckoutSessionModel).filter(CheckoutSessionModel.id == session_id).first()
