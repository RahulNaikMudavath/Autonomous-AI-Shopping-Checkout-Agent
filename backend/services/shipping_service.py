"""
Phase 2: Shipping & Delivery Quotation Service
Calculates server-side delivery quotes, estimates arrival dates, and validates shipping methods per merchant.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.database.models import ShippingOptionModel, MerchantModel
from backend.services.pricing_service import quantize_money, ZERO


class ShippingService:
    """
    Deterministic shipping quotation and carrier simulation service.
    """

    @staticmethod
    def get_shipping_options(db: Session, merchant_id: str) -> List[ShippingOptionModel]:
        """Returns all active shipping methods for a merchant."""
        return db.query(ShippingOptionModel).filter(
            ShippingOptionModel.merchant_id == merchant_id,
            ShippingOptionModel.is_active == True
        ).order_by(ShippingOptionModel.cost.asc()).all()

    @staticmethod
    def get_shipping_option_by_id(db: Session, option_id: str) -> Optional[ShippingOptionModel]:
        """Finds shipping option by ID."""
        return db.query(ShippingOptionModel).filter(
            ShippingOptionModel.id == option_id,
            ShippingOptionModel.is_active == True
        ).first()

    @staticmethod
    def calculate_shipping_cost(
        db: Session,
        merchant_id: str,
        shipping_option_id: Optional[str] = None,
        subtotal: Decimal = ZERO
    ) -> Decimal:
        """
        Determines the server-authoritative shipping fee.
        Applies merchant rules (e.g. Free standard shipping on orders >= ₹2,000).
        """
        if not shipping_option_id:
            # Default to cheapest active shipping option
            cheapest = db.query(ShippingOptionModel).filter(
                ShippingOptionModel.merchant_id == merchant_id,
                ShippingOptionModel.is_active == True
            ).order_by(ShippingOptionModel.cost.asc()).first()
            if not cheapest:
                return ZERO
            return quantize_money(cheapest.cost)

        option = db.query(ShippingOptionModel).filter(
            ShippingOptionModel.id == shipping_option_id,
            ShippingOptionModel.merchant_id == merchant_id,
            ShippingOptionModel.is_active == True
        ).first()

        if not option:
            return ZERO

        # Free shipping threshold for Standard orders above ₹2,000
        if option.code == "STANDARD" and subtotal >= Decimal("2000.00"):
            return ZERO

        return quantize_money(option.cost)

    @staticmethod
    def estimate_delivery_date(estimated_days: int) -> datetime:
        """Calculates expected delivery timestamp based on day count."""
        now = datetime.now(timezone.utc)
        return now + timedelta(days=max(1, estimated_days))
