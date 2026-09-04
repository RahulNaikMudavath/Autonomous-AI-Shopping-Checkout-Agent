"""
Phase 2: Pricing & Monetary Calculation Service
Enforces deterministic financial mathematics using exact Decimal representation.
Floating point operations are strictly prohibited in monetary computation.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.database.models import ProductModel, DiscountModel

# Standard 2-decimal money quantization
TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0.00")
GST_RATE = Decimal("0.18")  # 18% GST for Consumer Tech / Electronics


def quantize_money(amount: Decimal | float | int | str) -> Decimal:
    """Rounds an arbitrary numeric amount to standard 2-decimal currency representation."""
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


class PricingService:
    """
    Deterministic pricing and monetary policy engine.
    Calculates line totals, discounts, taxes, and grand totals with exact Decimal precision.
    """

    @staticmethod
    def calculate_line_item_total(unit_price: Decimal, quantity: int) -> Decimal:
        """Calculates line item total: unit_price * quantity."""
        if quantity <= 0:
            return ZERO
        u_price = quantize_money(unit_price)
        return quantize_money(u_price * Decimal(quantity))

    @staticmethod
    def calculate_subtotal(items: List[Tuple[Decimal, int]]) -> Decimal:
        """
        Calculates cart or order subtotal from a list of (unit_price, quantity) tuples.
        """
        subtotal = ZERO
        for unit_price, quantity in items:
            subtotal += PricingService.calculate_line_item_total(unit_price, quantity)
        return quantize_money(subtotal)

    @staticmethod
    def evaluate_discount(
        db: Session,
        merchant_id: str,
        promo_code: Optional[str],
        subtotal: Decimal
    ) -> Tuple[Decimal, Optional[DiscountModel]]:
        """
        Server-authoritative discount evaluation.
        Validates promo code against merchant, minimum order value, and applies percentage/flat discount.
        """
        if not promo_code:
            return ZERO, None

        code_clean = promo_code.strip().upper()
        discount = db.query(DiscountModel).filter(
            DiscountModel.merchant_id == merchant_id,
            DiscountModel.code == code_clean,
            DiscountModel.is_active == True
        ).first()

        if not discount:
            return ZERO, None

        subtotal_dec = quantize_money(subtotal)
        min_order_dec = quantize_money(discount.min_order_value)

        # Minimum order value threshold check
        if subtotal_dec < min_order_dec:
            return ZERO, None

        discount_amount = ZERO
        if discount.discount_type == "PERCENTAGE":
            pct = Decimal(str(discount.discount_value)) / Decimal("100.0")
            raw_discount = subtotal_dec * pct
            if discount.max_discount is not None:
                max_disc = quantize_money(discount.max_discount)
                raw_discount = min(raw_discount, max_disc)
            discount_amount = raw_discount
        elif discount.discount_type == "FLAT":
            discount_amount = quantize_money(discount.discount_value)

        # Discount cannot exceed subtotal
        discount_amount = min(discount_amount, subtotal_dec)
        return quantize_money(discount_amount), discount

    @staticmethod
    def calculate_tax(taxable_amount: Decimal, rate: Decimal = GST_RATE) -> Decimal:
        """Computes GST / tax on taxable amount."""
        if taxable_amount <= ZERO:
            return ZERO
        taxable = quantize_money(taxable_amount)
        return quantize_money(taxable * rate)

    @staticmethod
    def compute_grand_total(
        subtotal: Decimal,
        discount: Decimal = ZERO,
        shipping: Decimal = ZERO,
        tax: Decimal = ZERO
    ) -> Decimal:
        """
        Computes the final grand total: subtotal - discount + shipping + tax.
        Enforces non-negative total constraint.
        """
        sub = quantize_money(subtotal)
        disc = quantize_money(discount)
        ship = quantize_money(shipping)
        tx = quantize_money(tax)

        effective_base = max(ZERO, sub - disc)
        total = effective_base + ship + tx
        return quantize_money(total)
