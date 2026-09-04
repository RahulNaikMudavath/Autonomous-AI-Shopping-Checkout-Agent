"""
Phase 2: Checkout Preparation & Pre-Purchase Validation Service
Performs authoritative re-validation of inventory, pricing, promotions, and shipping before order placement.
Creates server-signed CheckoutSession records.
Enforces strict merchant isolation and server-authoritative calculations.
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
        5. Authoritatively evaluate and validate shipping option with strict merchant isolation.
        6. Compute applicable taxes (18% GST) and grand total.
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

        # 5. Authoritative Shipping Evaluation & Strict Merchant Boundary Isolation
        selected_shipping_opt = None
        shipping_cost = ZERO
        effective_shipping_option_id = None

        if request.shipping_option_id and request.shipping_option_id.strip():
            # Validate shipping option strictly belongs to cart's merchant
            shipping_option_model = ShippingService.validate_shipping_option_for_merchant(
                db=db,
                merchant_id=merchant.id,
                shipping_option_id=request.shipping_option_id.strip()
            )
            shipping_cost = ShippingService.calculate_shipping_cost_for_option(
                option=shipping_option_model,
                subtotal=subtotal
            )
            selected_shipping_opt = ShippingOptionDetail(
                id=shipping_option_model.id,
                merchant_id=shipping_option_model.merchant_id,
                code=shipping_option_model.code,
                name=shipping_option_model.name,
                cost=quantize_money(shipping_option_model.cost),
                estimated_days=shipping_option_model.estimated_days,
                delivery_type=shipping_option_model.delivery_type,
                is_active=shipping_option_model.is_active
            )
            effective_shipping_option_id = shipping_option_model.id
        else:
            # Default to cheapest active shipping option for the cart's merchant
            default_opt = db.query(ShippingOptionModel).filter(
                ShippingOptionModel.merchant_id == merchant.id,
                ShippingOptionModel.is_active == True
            ).order_by(ShippingOptionModel.cost.asc()).first()

            if default_opt:
                shipping_cost = ShippingService.calculate_shipping_cost_for_option(
                    option=default_opt,
                    subtotal=subtotal
                )
                selected_shipping_opt = ShippingOptionDetail(
                    id=default_opt.id,
                    merchant_id=default_opt.merchant_id,
                    code=default_opt.code,
                    name=default_opt.name,
                    cost=quantize_money(default_opt.cost),
                    estimated_days=default_opt.estimated_days,
                    delivery_type=default_opt.delivery_type,
                    is_active=default_opt.is_active
                )
                effective_shipping_option_id = default_opt.id
            else:
                shipping_cost = ZERO
                effective_shipping_option_id = None

        # 6. Tax & Grand Total Computation (Exact Formula: subtotal - discount + shipping + tax)
        taxable_base = max(ZERO, subtotal - discount_amount)
        tax_amount = PricingService.calculate_tax(taxable_base)
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
            shipping_option_id=effective_shipping_option_id,
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
            "Prepared CheckoutSession %s for merchant %s. Subtotal: ₹%s, Shipping: ₹%s, Tax: ₹%s, Grand Total: ₹%s",
            checkout_session.id, merchant.merchant_code, subtotal, shipping_cost, tax_amount, grand_total
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
