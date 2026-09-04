"""
Phase 2 & Phase 4: Multi-Merchant Shopping Cart Service
Enforces strict merchant boundary separation, item validation against stock, server-authoritative totals,
live price and inventory revalidation, and horizontal item ownership security.
"""
from decimal import Decimal
import logging
from typing import List, Optional, Tuple, Union
from sqlalchemy.orm import Session, joinedload

from backend.database.models import CartModel, CartItemModel, ProductModel, MerchantModel, InventoryModel
from backend.domain.marketplace import (
    CartDetail, CartItemDetail, CartStatus,
    RecommendationSelectionRequest, RecommendationSelectionResponse
)
from backend.services.pricing_service import PricingService, quantize_money, ZERO
from backend.services.inventory_service import InventoryService, OutOfStockException, InsufficientInventoryException
from backend.core.errors import AgentCartException, EntityNotFoundException

logger = logging.getLogger("agentcart.cart")


class CartService:
    """
    Manages stateful merchant-scoped carts and line items with server-authoritative integrity.
    """

    @classmethod
    def create_cart(cls, db: Session, merchant_id_or_code: str, session_id: Optional[str] = None) -> CartModel:
        """Creates a new isolated cart for a specific merchant."""
        merchant = db.query(MerchantModel).filter(
            (MerchantModel.id == merchant_id_or_code) |
            (MerchantModel.merchant_code == merchant_id_or_code.strip().upper())
        ).first()

        if not merchant:
            raise EntityNotFoundException("Merchant", merchant_id_or_code)

        if not merchant.is_active:
            raise AgentCartException(
                f"Merchant '{merchant.merchant_code}' is currently inactive.",
                code="MERCHANT_INACTIVE",
                status_code=400
            )

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
        logger.info("Created new cart %s for merchant %s (session=%s)", cart.id, merchant.merchant_code, session_id)
        return cart

    @classmethod
    def get_or_create_active_cart(
        cls,
        db: Session,
        merchant_id_or_code: str,
        session_id: Optional[str] = None
    ) -> CartModel:
        """
        Deterministically reuses an existing ACTIVE cart for the given merchant and session,
        or creates a new one if none exists.
        """
        merchant = db.query(MerchantModel).filter(
            (MerchantModel.id == merchant_id_or_code) |
            (MerchantModel.merchant_code == merchant_id_or_code.strip().upper())
        ).first()

        if not merchant:
            raise EntityNotFoundException("Merchant", merchant_id_or_code)

        if not merchant.is_active:
            raise AgentCartException(
                f"Merchant '{merchant.merchant_code}' is currently inactive.",
                code="MERCHANT_INACTIVE",
                status_code=400
            )

        cart = None
        if session_id:
            cart = db.query(CartModel).options(
                joinedload(CartModel.merchant),
                joinedload(CartModel.items).joinedload(CartItemModel.product)
            ).filter(
                CartModel.merchant_id == merchant.id,
                CartModel.session_id == session_id,
                CartModel.status == "ACTIVE"
            ).first()

        if not cart:
            cart = cls.create_cart(db, merchant.id, session_id)
        else:
            logger.info("Reusing existing active cart %s for merchant %s (session=%s)", cart.id, merchant.merchant_code, session_id)

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
        Recalculates cart subtotal and totals server-side based on actual live product catalog prices.
        Detects price changes, inactive products, and inventory stock changes.
        Attaches warnings and staleness flags directly to the CartModel instance.
        """
        warnings: List[str] = []
        is_stale = False
        subtotal = ZERO

        for item in cart.items:
            # Refresh live product information
            prod = item.product or db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
            if not prod:
                warnings.append(f"Product with ID '{item.product_id}' was not found in catalog.")
                is_stale = True
                continue

            if not prod.is_active:
                warnings.append(f"Product '{prod.title}' is no longer active for sale.")
                is_stale = True

            # Live price check
            live_price = quantize_money(prod.current_price)
            if item.unit_price != live_price:
                warnings.append(
                    f"Price for '{prod.title}' changed from ₹{item.unit_price:,.2f} to ₹{live_price:,.2f}."
                )
                item.unit_price = live_price
                is_stale = True

            # Recompute line item total
            item.total_price = PricingService.calculate_line_item_total(item.unit_price, item.quantity)
            subtotal += item.total_price

            # Live inventory check
            can_fulfill, avail_qty, _ = InventoryService.check_availability(db, prod.id, item.quantity)
            if not can_fulfill:
                is_stale = True
                if avail_qty == 0:
                    warnings.append(f"Product '{prod.title}' is currently out of stock.")
                else:
                    warnings.append(
                        f"Product '{prod.title}' has only {avail_qty} unit(s) available (in cart: {item.quantity})."
                    )

        cart.subtotal = quantize_money(subtotal)
        # Recompute grand total deterministically
        cart.grand_total = PricingService.compute_grand_total(
            subtotal=cart.subtotal,
            discount=cart.discount_total,
            shipping=cart.shipping_total,
            tax=cart.tax_total
        )
        cart.warnings = warnings
        cart.is_stale = is_stale
        db.flush()
        return cart

    @classmethod
    def add_item_to_cart(
        cls,
        db: Session,
        cart_id: str,
        product_id: str,
        quantity: int = 1,
        expected_price: Optional[Decimal] = None
    ) -> CartModel:
        """
        Adds or increments a product in the cart.
        Enforces that the product belongs to the cart's designated merchant and has sufficient inventory.
        """
        if quantity <= 0 or quantity > 100:
            raise AgentCartException("Quantity must be between 1 and 100.", code="INVALID_QUANTITY", status_code=400)

        cart = cls.get_cart(db, cart_id)
        if not cart:
            raise EntityNotFoundException("Cart", cart_id)

        if cart.status != "ACTIVE":
            raise AgentCartException(f"Cart '{cart_id}' is no longer active (status={cart.status}).", code="CART_INACTIVE", status_code=400)

        product = db.query(ProductModel).options(
            joinedload(ProductModel.merchant)
        ).filter(
            (ProductModel.id == product_id) | (ProductModel.sku == product_id)
        ).first()

        if not product:
            raise EntityNotFoundException("Product", product_id)

        if not product.is_active:
            raise AgentCartException(
                f"Product '{product.title}' (id={product.id}) is not active or available for sale.",
                code="PRODUCT_INACTIVE",
                status_code=400
            )

        # Enforce strict merchant boundary
        if product.merchant_id != cart.merchant_id:
            cart_merchant_name = cart.merchant.merchant_code if cart.merchant else cart.merchant_id
            prod_merchant_name = product.merchant.merchant_code if product.merchant else product.merchant_id
            raise AgentCartException(
                f"Cannot add product from merchant '{prod_merchant_name}' to cart belonging to merchant '{cart_merchant_name}'. "
                "AgentCart maintains distinct carts per merchant.",
                code="MERCHANT_MISMATCH",
                status_code=400
            )

        # Validate product price
        if product.current_price is None or product.current_price <= Decimal("0.00"):
            raise AgentCartException(
                f"Product '{product.title}' does not have a valid current price.",
                code="INVALID_PRICE",
                status_code=400
            )

        live_price = quantize_money(product.current_price)

        # Check existing item
        existing_item = next((it for it in cart.items if it.product_id == product.id), None)
        target_qty = (existing_item.quantity + quantity) if existing_item else quantity

        if target_qty > 100:
            raise AgentCartException("Total item quantity in cart cannot exceed 100 units.", code="INVALID_QUANTITY", status_code=400)

        # Verify stock availability
        can_fulfill, avail_qty, state = InventoryService.check_availability(db, product.id, target_qty)
        if not can_fulfill:
            if avail_qty == 0:
                raise OutOfStockException(product.id)
            raise InsufficientInventoryException(product.id, target_qty, avail_qty)

        if existing_item:
            existing_item.quantity = target_qty
            existing_item.unit_price = live_price
            existing_item.total_price = PricingService.calculate_line_item_total(live_price, target_qty)
        else:
            new_item = CartItemModel(
                cart_id=cart.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=live_price,
                total_price=PricingService.calculate_line_item_total(live_price, quantity)
            )
            db.add(new_item)
            cart.items.append(new_item)

        cls.recalculate_cart(db, cart)
        db.commit()
        db.refresh(cart)
        logger.info("Added %d units of product %s to cart %s", quantity, product.id, cart.id)
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
        Enforces item ownership (item.cart_id == cart.id).
        """
        if quantity < 0 or quantity > 100:
            raise AgentCartException("Quantity must be between 0 and 100.", code="INVALID_QUANTITY", status_code=400)

        cart = cls.get_cart(db, cart_id)
        if not cart:
            raise EntityNotFoundException("Cart", cart_id)

        if cart.status != "ACTIVE":
            raise AgentCartException(f"Cart '{cart_id}' is no longer active (status={cart.status}).", code="CART_INACTIVE", status_code=400)

        # Item ownership verification: item must belong to this specific cart
        item = next((it for it in cart.items if it.id == item_id or it.product_id == item_id), None)
        if not item:
            raise EntityNotFoundException("CartItem", item_id)

        if quantity <= 0:
            db.delete(item)
            cart.items.remove(item)
            logger.info("Removed item %s from cart %s via quantity=0 update", item_id, cart.id)
        else:
            # Check product active status
            prod = item.product or db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
            if not prod or not prod.is_active:
                raise AgentCartException("Product is inactive and cannot be updated.", code="PRODUCT_INACTIVE", status_code=400)

            # Check stock
            can_fulfill, avail_qty, _ = InventoryService.check_availability(db, item.product_id, quantity)
            if not can_fulfill:
                raise InsufficientInventoryException(item.product_id, quantity, avail_qty)

            item.quantity = quantity
            item.unit_price = quantize_money(prod.current_price)
            item.total_price = PricingService.calculate_line_item_total(item.unit_price, quantity)
            logger.info("Updated item %s quantity to %d in cart %s", item_id, quantity, cart.id)

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
        logger.info("Cleared all items from cart %s", cart.id)
        return cart

    @classmethod
    def to_dto(
        cls,
        cart: Union[CartModel, Tuple[CartModel, List[str], bool]],
        warnings: Optional[List[str]] = None,
        is_stale: bool = False,
        db: Optional[Session] = None
    ) -> CartDetail:
        """Converts CartModel into validated CartDetail DTO with live availability & merchant metadata."""
        if isinstance(cart, tuple):
            cart_obj, tuple_warnings, tuple_stale = cart
            return cls.to_dto(cart_obj, warnings=tuple_warnings or warnings, is_stale=tuple_stale or is_stale, db=db)

        warns = warnings if warnings is not None else getattr(cart, "warnings", [])
        stale = is_stale if is_stale else getattr(cart, "is_stale", False)

        items_dto = []
        for it in cart.items:
            prod = it.product
            is_avail = True
            avail_q = None
            if db:
                can_f, a_qty, _ = InventoryService.check_availability(db, it.product_id, it.quantity)
                is_avail = can_f and (prod.is_active if prod else True)
                avail_q = a_qty

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
                is_available=is_avail,
                available_quantity=avail_q,
                created_at=it.created_at.isoformat() if it.created_at else None
            ))

        return CartDetail(
            id=cart.id,
            merchant_id=cart.merchant_id,
            merchant_code=cart.merchant.merchant_code if cart.merchant else None,
            merchant_name=cart.merchant.display_name if cart.merchant else None,
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
            is_stale=stale,
            warnings=warns or [],
            created_at=cart.created_at.isoformat() if cart.created_at else None,
            updated_at=cart.updated_at.isoformat() if cart.updated_at else None
        )

    @classmethod
    def select_recommendation_and_add_to_cart(
        cls,
        db: Session,
        request: RecommendationSelectionRequest
    ) -> RecommendationSelectionResponse:
        """
        Phase 4 Step 1: Explicit Recommendation Selection -> Server-Authoritative Cart Mutation.
        Performs live database revalidation of:
        1. Quantity bounds (1 <= qty <= 100)
        2. Merchant existence & active status
        3. Product existence & active status
        4. Product merchant ownership matching
        5. Live price re-fetching from catalog
        6. Live inventory verification
        7. Merchant isolation cart retrieval or creation
        8. Recalculation of all subtotals, taxes, and grand totals
        """
        logger.info(
            "Processing recommendation selection: product_id=%s, merchant_code=%s, qty=%d, session_id=%s",
            request.product_id, request.merchant_code, request.quantity, request.session_id
        )

        # 1. Validate quantity
        if request.quantity <= 0 or request.quantity > 100:
            raise AgentCartException("Quantity must be between 1 and 100.", code="INVALID_QUANTITY", status_code=400)

        # 2. Validate Merchant existence and active status
        merchant = db.query(MerchantModel).filter(
            (MerchantModel.id == request.merchant_code) |
            (MerchantModel.merchant_code == request.merchant_code.strip().upper())
        ).first()

        if not merchant:
            raise EntityNotFoundException("Merchant", request.merchant_code)

        if not merchant.is_active:
            raise AgentCartException(
                f"Merchant '{merchant.merchant_code}' is currently inactive.",
                code="MERCHANT_INACTIVE",
                status_code=400
            )

        # 3. Validate Product existence and active status
        product = db.query(ProductModel).options(
            joinedload(ProductModel.merchant)
        ).filter(
            (ProductModel.id == request.product_id) | (ProductModel.sku == request.product_id)
        ).first()

        if not product:
            raise EntityNotFoundException("Product", request.product_id)

        if not product.is_active:
            raise AgentCartException(
                f"Product '{product.title}' (id={product.id}) is not active or available for sale.",
                code="PRODUCT_INACTIVE",
                status_code=400
            )

        # 4. Enforce strict merchant ownership match
        if product.merchant_id != merchant.id:
            raise AgentCartException(
                f"Product '{product.title}' belongs to merchant '{product.merchant.merchant_code if product.merchant else product.merchant_id}', "
                f"which does not match requested merchant '{merchant.merchant_code}'.",
                code="MERCHANT_MISMATCH",
                status_code=400
            )

        # 5. Live Price Validation
        if product.current_price is None or product.current_price <= Decimal("0.00"):
            raise AgentCartException(
                f"Product '{product.title}' does not have a valid current price.",
                code="INVALID_PRICE",
                status_code=400
            )

        live_price = quantize_money(product.current_price)
        price_changed = False
        if request.expected_price is not None:
            expected_quantized = quantize_money(request.expected_price)
            if live_price != expected_quantized:
                price_changed = True
                logger.info(
                    "Price change detected for product %s: expected=₹%s, live=₹%s",
                    product.id, expected_quantized, live_price
                )

        # 6. Locate or Create Isolated Merchant Cart
        cart = None
        if request.cart_id:
            cart = cls.get_cart(db, request.cart_id)
            if not cart:
                raise EntityNotFoundException("Cart", request.cart_id)
            if cart.merchant_id != merchant.id:
                raise AgentCartException(
                    f"Cannot add product from merchant '{merchant.merchant_code}' into existing cart belonging to '{cart.merchant.merchant_code if cart.merchant else cart.merchant_id}'. "
                    "Cross-merchant cart mutation is strictly prohibited.",
                    code="MERCHANT_MISMATCH",
                    status_code=400
                )
        else:
            cart = cls.get_or_create_active_cart(db, merchant.merchant_code, request.session_id)

        # 7. Live Inventory Verification
        existing_item = next((it for it in cart.items if it.product_id == product.id), None)
        target_qty = (existing_item.quantity + request.quantity) if existing_item else request.quantity

        if target_qty > 100:
            raise AgentCartException("Total item quantity in cart cannot exceed 100 units.", code="INVALID_QUANTITY", status_code=400)

        can_fulfill, avail_qty, state = InventoryService.check_availability(db, product.id, target_qty)
        if not can_fulfill:
            if avail_qty == 0:
                raise OutOfStockException(product.id)
            raise InsufficientInventoryException(product.id, target_qty, avail_qty)

        # 8. Mutate Cart Items
        if existing_item:
            existing_item.quantity = target_qty
            existing_item.unit_price = live_price
            existing_item.total_price = PricingService.calculate_line_item_total(live_price, target_qty)
        else:
            new_item = CartItemModel(
                cart_id=cart.id,
                product_id=product.id,
                quantity=request.quantity,
                unit_price=live_price,
                total_price=PricingService.calculate_line_item_total(live_price, request.quantity)
            )
            db.add(new_item)
            cart.items.append(new_item)

        # 9. Authoritative Server Recalculation
        cls.recalculate_cart(db, cart)
        db.commit()
        db.refresh(cart)

        cart_dto = cls.to_dto(cart, db=db)
        msg = f"Added {request.quantity} unit(s) of '{product.title}' to {merchant.merchant_code} cart."
        if price_changed:
            msg += f" Note: Price updated to ₹{live_price:,.2f} (previously displayed as ₹{request.expected_price:,.2f})."

        return RecommendationSelectionResponse(
            success=True,
            cart=cart_dto,
            price_changed=price_changed,
            original_expected_price=request.expected_price,
            current_authoritative_price=live_price,
            message=msg
        )
