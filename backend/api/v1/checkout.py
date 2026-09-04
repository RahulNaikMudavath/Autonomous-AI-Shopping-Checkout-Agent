"""
Phase 2 & Phase 4: Checkout Preparation API Endpoints
Provides authoritative pre-order revalidation, promotional code evaluation, and CheckoutSession / Quote creation.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db_session
from backend.database.models import MerchantModel
from backend.domain.marketplace import (
    CheckoutPrepareRequest, CheckoutSummaryResponse, ShippingOptionDetail
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
    summary="Prepare Checkout Quote / Session",
    description="Validates cart items against live inventory and catalog prices, evaluates promo discounts, checks shipping merchant boundaries, and generates an authoritative CheckoutSession quote."
)
def prepare_checkout(
    request: CheckoutPrepareRequest,
    db: Session = Depends(get_db_session)
) -> CheckoutSummaryResponse:
    return CheckoutService.prepare_checkout(db, request)


@checkout_router.get(
    "/checkout/{checkout_session_id}",
    response_model=CheckoutSummaryResponse,
    summary="Get Checkout Session / Quote",
    description="Retrieves an active or completed CheckoutSession summary with live staleness and expiration checks."
)
def get_checkout_session(
    checkout_session_id: str,
    db: Session = Depends(get_db_session)
) -> CheckoutSummaryResponse:
    summary = CheckoutService.get_checkout_session(db, checkout_session_id)
    if not summary:
        raise EntityNotFoundException("CheckoutSession", checkout_session_id)
    return summary


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
