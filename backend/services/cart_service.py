"""
Phase 2: Multi-Merchant Shopping Cart Service
Enforces strict merchant boundary separation, item validation against stock, and server-authoritative totals.
"""
from decimal import Decimal
import logging
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from backend.database.models import CartModel, CartItemModel, ProductModel, MerchantModel
from backend.domain.marketplace import CartDetail, CartItemDetail, CartStatus
from backend.services.pricing_service import PricingService, quantize_money, ZERO
from backend.services.inventory_service import InventoryService, OutOfStockException, InsufficientInventoryException
from backend.core.errors import AgentCartException, EntityNotFoundException

logger = logging.getLogger("agentcart.cart")


class CartService:
    """
    Manages stateful merchant-scoped carts and line items.
    """

    @staticmethod
    def create_cart(db: Session, merchant_id_or_code: str, session_id: Optional[str] = None) -> CartModel:
        """Creates a new isolated cart for a specific merchant."""
        merchant = db.query(MerchantModel).filter(
            (MerchantModel.id == merchant_id_or_code) |
            (MerchantModel.merchant_code == merchant_id_or_code.strip().upper())
        ).first()

        if not merchant:
            raise EntityNotFoundException("Merchant", merchant_id_or_code)

        cart = CartModel(
            merchant_id=merchant.id,
            session_id=session_id,
            subtotal=ZERO,
            discount_total=ZERO,
            shipping_total=ZERO,
            tax_total=ZERO,
            grand_total=ZERO,
            currency="INR",
            status="ACTIVE"
        )
        db.add(cart)
        db.commit()
        db.refresh(cart)
        logger.info("Created cart %s for merchant %s", cart.id, merchant.merchant_code)
        return cart

    @staticmethod
    def get_cart(db: Session, cart_id: str) -> Optional[CartModel]:
        """Fetches cart with items and merchant eagerly loaded."""
        return db.query(CartModel).options(
            joinedload(CartModel.merchant),
            joinedload(CartModel.items).joinedload(CartItemModel.product)
        ).filter(
            CartModel.id == cart_id,
            CartModel.status == "ACTIVE"
        ).first()

    @classmethod
    def recalculate_cart(cls, db: Session, cart: CartModel) -> CartModel:
        """
        Recalculates cart subtotal and totals server-side based on actual product catalog prices.
        """
        subtotal = ZERO
        for item in cart.items:
            # Refresh price from product
            prod = item.product or db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
            if prod:
                item.unit_price = quantize_money(prod.current_price)
                item.total_price = PricingService.calculate_line_item_total(item.unit_price, item.quantity)
                subtotal += item.total_price

        cart.subtotal = quantize_money(subtotal)
        # Recompute grand total
        cart.grand_total = PricingService.compute_grand_total(
            subtotal=cart.subtotal,
            discount=cart.discount_total,
            shipping=cart.shipping_total,
            tax=cart.tax_total
        )
        db.flush()
        return cart

    @classmethod
    def add_item_to_cart(
        cls,
        db: Session,
        cart_id: str,
        product_id: str,
        quantity: int = 1
    ) -> CartModel:
        """
        Adds or increments a product in the cart.
        Enforces that the product belongs to the cart's designated merchant and has sufficient inventory.
        """
        if quantity <= 0:
            raise AgentCartException("Quantity must be greater than zero.", code="INVALID_QUANTITY", status_code=400)

        cart = cls.get_cart(db, cart_id)
        if not cart:
            raise EntityNotFoundException("Cart", cart_id)

        product = db.query(ProductModel).filter(
            ProductModel.id == product_id,
            ProductModel.is_active == True
        ).first()
        if not product:
            raise EntityNotFoundException("Product", product_id)

        # Enforce merchant boundary
        if product.merchant_id != cart.merchant_id:
            raise AgentCartException(
                f"Cannot add product from merchant '{product.merchant_id}' to cart belonging to merchant '{cart.merchant_id}'. "
                "AgentCart maintains distinct carts per merchant.",
                code="MERCHANT_MISMATCH",
                status_code=400
            )

        # Check existing item
        existing_item = next((it for it in cart.items if it.product_id == product_id), None)
        target_qty = (existing_item.quantity + quantity) if existing_item else quantity

        # Verify stock availability
        can_fulfill, avail_qty, state = InventoryService.check_availability(db, product_id, target_qty)
        if not can_fulfill:
            if avail_qty == 0:
                raise OutOfStockException(product_id)
            raise InsufficientInventoryException(product_id, target_qty, avail_qty)

        unit_p = quantize_money(product.current_price)
        if existing_item:
            existing_item.quantity = target_qty
            existing_item.unit_price = unit_p
            existing_item.total_price = PricingService.calculate_line_item_total(unit_p, target_qty)
        else:
            new_item = CartItemModel(
                cart_id=cart.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_p,
                total_price=PricingService.calculate_line_item_total(unit_p, quantity)
            )
            db.add(new_item)
            cart.items.append(new_item)

        cls.recalculate_cart(db, cart)
        db.commit()
        db.refresh(cart)
        return cart

    @classmethod
    def update_cart_item(
        cls,
        db: Session,
        cart_id: str,
        item_id: str,
        quantity: int
    ) -> CartModel:
        """
        Updates quantity for a cart line item.
        If quantity is 0, removes the item.
        """
        cart = cls.get_cart(db, cart_id)
        if not cart:
            raise EntityNotFoundException("Cart", cart_id)

        item = next((it for it in cart.items if it.id == item_id or it.product_id == item_id), None)
        if not item:
            raise EntityNotFoundException("CartItem", item_id)

        if quantity <= 0:
            db.delete(item)
            cart.items.remove(item)
        else:
            # Check stock
            can_fulfill, avail_qty, _ = InventoryService.check_availability(db, item.product_id, quantity)
            if not can_fulfill:
                raise InsufficientInventoryException(item.product_id, quantity, avail_qty)

            item.quantity = quantity
            item.total_price = PricingService.calculate_line_item_total(item.unit_price, quantity)

        cls.recalculate_cart(db, cart)
        db.commit()
        db.refresh(cart)
        return cart

    @classmethod
    def remove_cart_item(cls, db: Session, cart_id: str, item_id: str) -> CartModel:
        """Removes a specific line item from the cart."""
        return cls.update_cart_item(db, cart_id, item_id, quantity=0)

    @classmethod
    def clear_cart(cls, db: Session, cart_id: str) -> CartModel:
        """Removes all items from the cart and resets totals."""
        cart = cls.get_cart(db, cart_id)
        if not cart:
            raise EntityNotFoundException("Cart", cart_id)

        for item in list(cart.items):
            db.delete(item)
        cart.items = []
        cart.subtotal = ZERO
        cart.discount_total = ZERO
        cart.shipping_total = ZERO
        cart.tax_total = ZERO
        cart.grand_total = ZERO

        db.commit()
        db.refresh(cart)
        return cart

    @classmethod
    def to_dto(cls, cart: CartModel) -> CartDetail:
        """Converts CartModel into validated CartDetail DTO."""
        items_dto = []
        for it in cart.items:
            prod = it.product
            items_dto.append(CartItemDetail(
                id=it.id,
                cart_id=it.cart_id,
                product_id=it.product_id,
                product_title=prod.title if prod else None,
                sku=prod.sku if prod else None,
                image_url=prod.image_url if prod else None,
                quantity=it.quantity,
                unit_price=quantize_money(it.unit_price),
                total_price=quantize_money(it.total_price),
                created_at=it.created_at.isoformat() if it.created_at else None
            ))

        return CartDetail(
            id=cart.id,
            merchant_id=cart.merchant_id,
            merchant_code=cart.merchant.merchant_code if cart.merchant else None,
            session_id=cart.session_id,
            items=items_dto,
            items_count=sum(it.quantity for it in cart.items),
            subtotal=quantize_money(cart.subtotal),
            discount_total=quantize_money(cart.discount_total),
            shipping_total=quantize_money(cart.shipping_total),
            tax_total=quantize_money(cart.tax_total),
            grand_total=quantize_money(cart.grand_total),
            currency=cart.currency,
            status=CartStatus(cart.status),
            created_at=cart.created_at.isoformat() if cart.created_at else None,
            updated_at=cart.updated_at.isoformat() if cart.updated_at else None
        )
