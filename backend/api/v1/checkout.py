"""
Phase 2: Checkout Preparation API Endpoints
Provides authoritative pre-order revalidation, promotional code evaluation, and CheckoutSession creation.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db_session
from backend.database.models import MerchantModel, ShippingOptionModel
from backend.domain.marketplace import (
    CheckoutPrepareRequest, CheckoutSummaryResponse, ShippingOptionDetail,
    CheckoutSessionStatus, CheckoutItemSummary
)
from backend.services.checkout_service import CheckoutService
from backend.services.shipping_service import ShippingService
from backend.services.pricing_service import quantize_money
from backend.core.errors import EntityNotFoundException

checkout_router = APIRouter(tags=["Checkout & Shipping"])


@checkout_router.post(
    "/checkout/prepare",
    response_model=CheckoutSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Prepare Checkout Session",
    description="Validates cart items against live inventory and catalog prices, evaluates promo discounts, and generates a CheckoutSession."
)
def prepare_checkout(
    request: CheckoutPrepareRequest,
    db: Session = Depends(get_db_session)
) -> CheckoutSummaryResponse:
    return CheckoutService.prepare_checkout(db, request)


@checkout_router.get(
    "/checkout/{checkout_session_id}",
    response_model=CheckoutSummaryResponse,
    summary="Get Checkout Session",
    description="Retrieves an active or completed CheckoutSession summary."
)
def get_checkout_session(
    checkout_session_id: str,
    db: Session = Depends(get_db_session)
) -> CheckoutSummaryResponse:
    session = CheckoutService.get_checkout_session(db, checkout_session_id)
    if not session:
        raise EntityNotFoundException("CheckoutSession", checkout_session_id)

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

    return CheckoutSummaryResponse(
        checkout_session_id=session.id,
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
        status=CheckoutSessionStatus(session.status),
        expires_at=session.expires_at.isoformat(),
        created_at=session.created_at.isoformat()
    )


@checkout_router.get(
    "/shipping-options",
    response_model=List[ShippingOptionDetail],
    summary="Get Shipping Options",
    description="Lists active shipping methods and rates for a specified merchant."
)
def get_shipping_options(
    merchant_code: str = Query(..., description="Merchant code (e.g. AMAZON, FLIPKART, CROMA)"),
    db: Session = Depends(get_db_session)
) -> List[ShippingOptionDetail]:
    clean = merchant_code.strip().upper()
    merchant = db.query(MerchantModel).filter(
        (MerchantModel.merchant_code == clean) | (MerchantModel.id == clean),
        MerchantModel.is_active == True
    ).first()
    if not merchant:
        raise EntityNotFoundException("Merchant", merchant_code)

    options = ShippingService.get_shipping_options(db, merchant.id)
    return [
        ShippingOptionDetail(
            id=opt.id,
            merchant_id=opt.merchant_id,
            code=opt.code,
            name=opt.name,
            cost=quantize_money(opt.cost),
            estimated_days=opt.estimated_days,
            delivery_type=opt.delivery_type,
            is_active=opt.is_active
        )
        for opt in options
    ]
