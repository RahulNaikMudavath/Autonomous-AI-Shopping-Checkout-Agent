"""
Phase 2: Merchant API Endpoints
Provides endpoints to inspect simulated merchants, their active capabilities, ratings, and policies.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database.session import get_db_session
from backend.database.models import MerchantModel, ProductModel, ShippingOptionModel, DiscountModel
from backend.domain.marketplace import MerchantSummary, MerchantDetail
from backend.core.errors import EntityNotFoundException

merchants_router = APIRouter(prefix="/merchants", tags=["Merchants"])


@merchants_router.get(
    "",
    response_model=List[MerchantSummary],
    summary="List Active Merchants",
    description="Returns all registered active simulated merchants in the marketplace (e.g. Amazon, Flipkart, Croma)."
)
def list_merchants(db: Session = Depends(get_db_session)) -> List[MerchantSummary]:
    merchants = db.query(MerchantModel).filter(MerchantModel.is_active == True).order_by(MerchantModel.display_name.asc()).all()
    return [
        MerchantSummary(
            id=m.id,
            merchant_code=m.merchant_code,
            display_name=m.display_name,
            description=m.description,
            is_active=m.is_active,
            rating=m.rating,
            logo_url=m.logo_url,
            capabilities=m.capabilities or []
        )
        for m in merchants
    ]


@merchants_router.get(
    "/{merchant_id_or_code}",
    response_model=MerchantDetail,
    summary="Get Merchant Details",
    description="Retrieves comprehensive operational metadata, active catalog size, and capabilities for a merchant."
)
def get_merchant_detail(
    merchant_id_or_code: str,
    db: Session = Depends(get_db_session)
) -> MerchantDetail:
    clean = merchant_id_or_code.strip()
    merchant = db.query(MerchantModel).filter(
        (MerchantModel.id == clean) |
        (MerchantModel.merchant_code == clean.upper()),
        MerchantModel.is_active == True
    ).first()

    if not merchant:
        raise EntityNotFoundException("Merchant", merchant_id_or_code)

    products_cnt = db.query(ProductModel).filter(ProductModel.merchant_id == merchant.id, ProductModel.is_active == True).count()
    shipping_cnt = db.query(ShippingOptionModel).filter(ShippingOptionModel.merchant_id == merchant.id, ShippingOptionModel.is_active == True).count()
    discounts_cnt = db.query(DiscountModel).filter(DiscountModel.merchant_id == merchant.id, DiscountModel.is_active == True).count()

    return MerchantDetail(
        id=merchant.id,
        merchant_code=merchant.merchant_code,
        display_name=merchant.display_name,
        description=merchant.description,
        is_active=merchant.is_active,
        rating=merchant.rating,
        logo_url=merchant.logo_url,
        capabilities=merchant.capabilities or [],
        active_products_count=products_cnt,
        shipping_options_count=shipping_cnt,
        active_promotions_count=discounts_cnt,
        created_at=merchant.created_at.isoformat() if merchant.created_at else None,
        updated_at=merchant.updated_at.isoformat() if merchant.updated_at else None
    )
