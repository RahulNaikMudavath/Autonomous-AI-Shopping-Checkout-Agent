"""
Phase 2 & Phase 4: Checkout Preparation & Pre-Purchase Validation Service (Checkout Quote Engine)
Performs authoritative live re-validation of inventory, catalog pricing, promotions, and shipping before authorization.
Creates server-signed CheckoutSession quote records with bounded 15-minute TTL.
Enforces strict merchant isolation and 100% server-authoritative calculations.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging
from typing import Dict, List, Optional, Tuple
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
    Coordinates server-authoritative pre-checkout verification and checkout quote generation.
    """

    @classmethod
    def prepare_checkout(
        cls,
        db: Session,
        request: CheckoutPrepareRequest
    ) -> CheckoutSummaryResponse:
        """
        Executes the deterministic 9-step checkout quote preparation workflow:
        1. Retrieve cart, verify active status, and verify non-empty.
        2. Validate merchant existence and active status.
        3. Validate every product is active and belongs to the cart merchant.
        4. Re-check live inventory availability for all items (zero inventory decrement).
        5. Revalidate live product catalog prices (detect price changes without trusting stored price).
        6. Authoritatively evaluate promotional discounts.
        7. Authoritatively validate shipping option with strict merchant isolation (reject cross-merchant shipping).
        8. Compute applicable taxes (18% GST) and grand total with Decimal precision.
        9. Persist CheckoutSession quote record with bounded 15-minute TTL.
        """
        # 1. Cart Verification
        cart = db.query(CartModel).options(
            joinedload(CartModel.merchant),
            joinedload(CartModel.items).joinedload(CartItemModel.product)
        ).filter(
            CartModel.id == request.cart_id
        ).first()

        if not cart:
            raise EntityNotFoundException("Cart", request.cart_id)

        if cart.status != "ACTIVE":
            raise AgentCartException(
                f"Cart '{cart.id}' is not active (status={cart.status}).",
                code="CART_INACTIVE",
                status_code=400
            )

        if not cart.items or len(cart.items) == 0:
            raise CheckoutValidationException("Cannot prepare checkout for an empty cart.", code="EMPTY_CART")

        # 2. Merchant Verification
        merchant = cart.merchant or db.query(MerchantModel).filter(MerchantModel.id == cart.merchant_id).first()
        if not merchant:
            raise EntityNotFoundException("Merchant", cart.merchant_id)

        if not merchant.is_active:
            raise AgentCartException(
                f"Merchant '{merchant.merchant_code}' is currently inactive.",
                code="MERCHANT_INACTIVE",
                status_code=400
            )

        items_snapshot = []
        item_tuples = []
        item_summaries = []
        price_changed = False
        warnings: List[str] = []

        # 3, 4, 5. Product, Inventory & Live Price Revalidation
        for it in cart.items:
            prod = it.product or db.query(ProductModel).filter(ProductModel.id == it.product_id).first()
            if not prod:
                raise EntityNotFoundException("Product", it.product_id)

            if not prod.is_active:
                raise AgentCartException(
                    f"Product '{prod.title}' (id={prod.id}) is no longer active for sale.",
                    code="PRODUCT_INACTIVE",
                    status_code=400,
                    details={"product_id": prod.id}
                )

            # Strict product merchant boundary check
            if prod.merchant_id != cart.merchant_id:
                raise AgentCartException(
                    f"Product '{prod.title}' belongs to merchant '{prod.merchant_id}', not cart merchant '{merchant.merchant_code}'. "
                    "Cross-merchant checkout quote is strictly prohibited.",
                    code="MERCHANT_MISMATCH",
                    status_code=400
                )

            # Check live inventory availability
            can_fulfill, avail_qty, state = InventoryService.check_availability(db, prod.id, it.quantity)
            if not can_fulfill:
                if avail_qty == 0:
                    raise OutOfStockException(prod.id, message=f"Item '{prod.title}' is currently out of stock.")
                raise InsufficientInventoryException(prod.id, it.quantity, avail_qty)

            # Live price revalidation against catalog
            if prod.current_price is None or prod.current_price <= Decimal("0.00"):
                raise AgentCartException(
                    f"Product '{prod.title}' does not have a valid catalog price.",
                    code="INVALID_PRICE",
                    status_code=400
                )

            live_u_price = quantize_money(prod.current_price)
            cart_u_price = quantize_money(it.unit_price)

            if live_u_price != cart_u_price:
                price_changed = True
                warnings.append(
                    f"Price for '{prod.title}' was updated to live catalog price ₹{live_u_price:,.2f} (cart had ₹{cart_u_price:,.2f})."
                )
                it.unit_price = live_u_price
                it.total_price = PricingService.calculate_line_item_total(live_u_price, it.quantity)

            line_total = PricingService.calculate_line_item_total(live_u_price, it.quantity)
            item_tuples.append((live_u_price, it.quantity))

            items_snapshot.append({
                "product_id": prod.id,
                "product_title": prod.title,
                "sku": prod.sku,
                "quantity": it.quantity,
                "unit_price": str(live_u_price),
                "total_price": str(line_total)
            })
            item_summaries.append(CheckoutItemSummary(
                product_id=prod.id,
                product_title=prod.title,
                sku=prod.sku,
                quantity=it.quantity,
                unit_price=live_u_price,
                total_price=line_total
            ))

        subtotal = PricingService.calculate_subtotal(item_tuples)

        # 6. Authoritative Discount Evaluation
        discount_amount, discount_model = PricingService.evaluate_discount(
            db=db,
            merchant_id=merchant.id,
            promo_code=request.promo_code,
            subtotal=subtotal
        )

        # 7. Authoritative Shipping Evaluation & Strict Merchant Boundary Isolation
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

        # 8. Tax & Grand Total Computation (Exact Formula: subtotal - discount + shipping + tax)
        taxable_base = max(ZERO, subtotal - discount_amount)
        tax_amount = PricingService.calculate_tax(taxable_base)
        grand_total = PricingService.compute_grand_total(
            subtotal=subtotal,
            discount=discount_amount,
            shipping=shipping_cost,
            tax=tax_amount
        )

        # 9. Persist Checkout Quote Session with 15-minute TTL
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=CHECKOUT_EXPIRATION_MINUTES)

        checkout_session = CheckoutSessionModel(
            cart_id=cart.id,
            merchant_id=merchant.id,
            session_id=request.session_id or cart.session_id,
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
            "Generated authoritative checkout quote %s for merchant %s. Subtotal: ₹%s, Discount: ₹%s, Shipping: ₹%s, Tax: ₹%s, Grand Total: ₹%s",
            checkout_session.id, merchant.merchant_code, subtotal, discount_amount, shipping_cost, tax_amount, grand_total
        )

        return CheckoutSummaryResponse(
            checkout_session_id=checkout_session.id,
            quote_id=checkout_session.id,
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
            price_changed=price_changed,
            is_stale=False,
            warnings=warnings,
            expires_at=expires_at.isoformat(),
            created_at=now.isoformat()
        )

    @classmethod
    def get_checkout_session(cls, db: Session, session_id: str) -> Optional[CheckoutSummaryResponse]:
        """
        Retrieves checkout session by ID with authoritative staleness and expiration verification.
        """
        session = db.query(CheckoutSessionModel).filter(CheckoutSessionModel.id == session_id).first()
        if not session:
            return None

        merchant = db.query(MerchantModel).filter(MerchantModel.id == session.merchant_id).first()
        shipping_opt = None
        if session.shipping_option_id:
            opt = db.query(ShippingOptionModel).filter(ShippingOptionModel.id == session.shipping_option_id).first()
            if opt:
                shipping_opt = ShippingOptionDetail(
                    id=opt.id,
                    merchant_id=opt.merchant_id,
                    code=opt.code,
                    name=opt.name,
                    cost=quantize_money(opt.cost),
                    estimated_days=opt.estimated_days,
                    delivery_type=opt.delivery_type,
                    is_active=opt.is_active
                )

        items = [
            CheckoutItemSummary(
                product_id=it.get("product_id", ""),
                product_title=it.get("product_title", "Product"),
                sku=it.get("sku", ""),
                quantity=int(it.get("quantity", 1)),
                unit_price=quantize_money(it.get("unit_price", "0.00")),
                total_price=quantize_money(it.get("total_price", "0.00"))
            )
            for it in (session.items_snapshot or [])
        ]

        # Check expiration
        now = datetime.now(timezone.utc)
        is_expired = now > session.expires_at if session.expires_at else False
        is_stale = False
        warnings = []

        if is_expired:
            session.status = "EXPIRED"
            db.commit()
            warnings.append("This checkout quote has expired. Please generate a fresh quote.")

        # Check underlying cart staleness
        cart = db.query(CartModel).filter(CartModel.id == session.cart_id).first()
        if cart and cart.updated_at and cart.updated_at > session.created_at:
            is_stale = True
            warnings.append("The underlying shopping cart was modified after this quote was created. Please refresh.")

        status_enum = CheckoutSessionStatus.EXPIRED if is_expired else CheckoutSessionStatus(session.status)

        return CheckoutSummaryResponse(
            checkout_session_id=session.id,
            quote_id=session.id,
            cart_id=session.cart_id,
            merchant_code=merchant.merchant_code if merchant else "MERCHANT",
            merchant_name=merchant.display_name if merchant else "Merchant",
            subtotal=quantize_money(session.subtotal),
            discount_total=quantize_money(session.discount_total),
            shipping_total=quantize_money(session.shipping_total),
            tax_total=quantize_money(session.tax_total),
            grand_total=quantize_money(session.grand_total),
            currency=session.currency,
            items=items,
            shipping_option=shipping_opt,
            applied_promo=session.promo_code,
            status=status_enum,
            price_changed=False,
            is_stale=is_stale,
            warnings=warnings,
            expires_at=session.expires_at.isoformat() if session.expires_at else now.isoformat(),
            created_at=session.created_at.isoformat() if session.created_at else now.isoformat()
        )
