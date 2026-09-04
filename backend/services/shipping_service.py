"""
Phase 2: Shipping & Delivery Quotation Service
Calculates server-side delivery quotes, estimates arrival dates, and validates shipping methods per merchant.
Enforces strict cross-merchant isolation on all shipping options.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.database.models import ShippingOptionModel, MerchantModel
from backend.services.pricing_service import quantize_money, ZERO
from backend.core.errors import AgentCartException, EntityNotFoundException


class ShippingService:
    """
    Deterministic shipping quotation and carrier simulation service.
    Enforces strict merchant isolation and server-authoritative fee computation.
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

    @classmethod
    def validate_shipping_option_for_merchant(
        cls,
        db: Session,
        merchant_id: str,
        shipping_option_id: str
    ) -> ShippingOptionModel:
        """
        Validates that a requested shipping option exists, is active,
        and strictly belongs to the specified cart merchant.
        Raises MERCHANT_MISMATCH (400) if cross-merchant option is passed.
        """
        clean_id = shipping_option_id.strip()

        # Lookup by primary key ID or by code within this merchant
        option = db.query(ShippingOptionModel).filter(
            ShippingOptionModel.id == clean_id
        ).first()

        if not option:
            # Check if code was passed instead of UUID (e.g. "PRIME_EXPRESS", "STANDARD")
            option_by_code = db.query(ShippingOptionModel).filter(
                ShippingOptionModel.code == clean_id.upper(),
                ShippingOptionModel.merchant_id == merchant_id,
                ShippingOptionModel.is_active == True
            ).first()
            if option_by_code:
                return option_by_code

            # Check if code exists on a different merchant
            other_option_by_code = db.query(ShippingOptionModel).filter(
                ShippingOptionModel.code == clean_id.upper()
            ).first()
            if other_option_by_code:
                raise AgentCartException(
                    f"Shipping option code '{clean_id}' does not belong to cart merchant '{merchant_id}'. "
                    f"Cross-merchant shipping options are strictly prohibited.",
                    code="MERCHANT_MISMATCH",
                    status_code=400,
                    details={
                        "shipping_option_code": clean_id,
                        "cart_merchant_id": merchant_id,
                        "option_merchant_id": other_option_by_code.merchant_id
                    }
                )

            raise EntityNotFoundException("ShippingOption", shipping_option_id)

        # Enforce merchant boundary isolation
        if option.merchant_id != merchant_id:
            raise AgentCartException(
                f"Shipping option '{option.name}' ({option.id}) belongs to merchant '{option.merchant_id}', "
                f"not cart merchant '{merchant_id}'. Cross-merchant shipping options are strictly prohibited.",
                code="MERCHANT_MISMATCH",
                status_code=400,
                details={
                    "shipping_option_id": option.id,
                    "shipping_option_name": option.name,
                    "cart_merchant_id": merchant_id,
                    "option_merchant_id": option.merchant_id
                }
            )

        if not option.is_active:
            raise AgentCartException(
                f"Shipping option '{option.name}' is currently inactive.",
                code="INACTIVE_SHIPPING_OPTION",
                status_code=400,
                details={"shipping_option_id": option.id}
            )

        return option

    @staticmethod
    def calculate_shipping_cost_for_option(
        option: ShippingOptionModel,
        subtotal: Decimal = ZERO
    ) -> Decimal:
        """
        Determines the server-authoritative shipping fee for a validated shipping option.
        Applies merchant rules (e.g. Free standard shipping on orders >= ₹2,000).
        """
        opt_cost = quantize_money(option.cost)
        # Free shipping threshold for Standard orders above ₹2,000
        if option.code == "STANDARD" and subtotal >= Decimal("2000.00"):
            return ZERO
        return opt_cost

    @classmethod
    def calculate_shipping_cost(
        cls,
        db: Session,
        merchant_id: str,
        shipping_option_id: Optional[str] = None,
        subtotal: Decimal = ZERO
    ) -> Decimal:
        """
        Determines the server-authoritative shipping fee.
        Validates merchant isolation if shipping_option_id is provided.
        """
        if not shipping_option_id:
            # Default to cheapest active shipping option
            cheapest = db.query(ShippingOptionModel).filter(
                ShippingOptionModel.merchant_id == merchant_id,
                ShippingOptionModel.is_active == True
            ).order_by(ShippingOptionModel.cost.asc()).first()
            if not cheapest:
                return ZERO
            return cls.calculate_shipping_cost_for_option(cheapest, subtotal)

        option = cls.validate_shipping_option_for_merchant(db, merchant_id, shipping_option_id)
        return cls.calculate_shipping_cost_for_option(option, subtotal)

    @staticmethod
    def estimate_delivery_date(estimated_days: int) -> datetime:
        """Calculates expected delivery timestamp based on day count."""
        now = datetime.now(timezone.utc)
        return now + timedelta(days=max(1, estimated_days))
