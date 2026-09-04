"""
Layer 4: Commerce Infrastructure - Cart & Order Engine
Handles stateful carts, tokenized checkout quotes, payment execution simulation, and order lifecycle.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from backend.schemas import Product, Cart, CartItem, CheckoutQuote, Order, PolicyCheckResult

# In-memory stores
CARTS: Dict[str, Cart] = {}
ORDERS: Dict[str, Order] = {}

def get_or_create_cart(cart_id: Optional[str] = None) -> Cart:
    if not cart_id or cart_id not in CARTS:
        cid = cart_id or f"cart_{uuid.uuid4().hex[:8]}"
        cart = Cart(
            cart_id=cid,
            items=[],
            subtotal_inr=0.0,
            shipping_total_inr=0.0,
            tax_total_inr=0.0,
            discount_total_inr=0.0,
            grand_total_inr=0.0
        )
        CARTS[cid] = cart
        return cart
    return CARTS[cart_id]

def add_to_cart(cart_id: str, product: Product, quantity: int = 1) -> Cart:
    cart = get_or_create_cart(cart_id)
    
    # Check if product already exists
    existing = next((item for item in cart.items if item.product.id == product.id), None)
    if existing:
        existing.quantity += quantity
        existing.total_price_inr = existing.quantity * existing.unit_price_inr
    else:
        cart.items.append(CartItem(
            product=product,
            quantity=quantity,
            selected_merchant_id=product.merchant_id,
            unit_price_inr=product.price_inr,
            total_price_inr=product.price_inr * quantity
        ))
    
    _recalculate_cart_totals(cart)
    return cart

def remove_from_cart(cart_id: str, product_id: str) -> Cart:
    cart = get_or_create_cart(cart_id)
    cart.items = [item for item in cart.items if item.product.id != product_id]
    _recalculate_cart_totals(cart)
    return cart

def clear_cart(cart_id: str) -> Cart:
    cart = get_or_create_cart(cart_id)
    cart.items = []
    _recalculate_cart_totals(cart)
    return cart

def _recalculate_cart_totals(cart: Cart):
    subtotal = sum(item.total_price_inr for item in cart.items)
    shipping = sum(item.product.shipping_fee_inr for item in cart.items)
    tax = round(subtotal * 0.18, 2) # 18% GST standard in India
    # 5% auto promotional discount if subtotal > 1 lakh
    discount = round(subtotal * 0.05, 2) if subtotal >= 100000 else 0.0
    grand_total = subtotal + shipping + tax - discount
    
    cart.subtotal_inr = subtotal
    cart.shipping_total_inr = shipping
    cart.tax_total_inr = tax
    cart.discount_total_inr = discount
    cart.grand_total_inr = grand_total

def create_checkout_quote(cart_id: str, policy_check: PolicyCheckResult) -> CheckoutQuote:
    cart = get_or_create_cart(cart_id)
    if not cart.items:
        raise ValueError("Cannot create checkout quote for empty cart")
        
    first_product = cart.items[0].product
    quote_id = f"quote_{uuid.uuid4().hex[:8]}"
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    
    return CheckoutQuote(
        quote_id=quote_id,
        cart_id=cart.cart_id,
        product_title=first_product.title if len(cart.items) == 1 else f"{first_product.title} + {len(cart.items)-1} more items",
        merchant_name=first_product.merchant_name,
        amount_inr=cart.grand_total_inr,
        breakdown={
            "subtotal": cart.subtotal_inr,
            "gst_18pct": cart.tax_total_inr,
            "shipping": cart.shipping_total_inr,
            "ai_coupon_discount": -cart.discount_total_inr
        },
        tokenized_payment_methods=["UPI_TOKEN_VPA_4921", "TOKENIZED_VISA_PREMIUM_9912"],
        policy_check=policy_check,
        expires_at=expires_at
    )

def execute_order_checkout(
    product: Product,
    payment_method: str = "UPI (Tokenized)",
    shipping_address: str = "Rahul N., Flat 402, HighTech Tech Park, Bangalore 560100",
    audit_hash: str = "",
    quote: Optional[CheckoutQuote] = None
) -> Order:
    order_id = f"ORD_{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)
    eta = (now + timedelta(days=product.delivery_days)).strftime("%A, %B %d, %Y")
    amount = quote.amount_inr if quote is not None else product.price_inr
    
    order = Order(
        order_id=order_id,
        merchant_id=product.merchant_id,
        merchant_name=product.merchant_name,
        product=product,
        amount_inr=amount,
        payment_method=payment_method,
        payment_status="AUTHORIZED",
        order_status="CONFIRMED",
        tracking_id=f"TRK-BLR-{uuid.uuid4().hex[:6].upper()}",
        estimated_delivery=eta,
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
        shipping_address=shipping_address,
        audit_block_hash=audit_hash
    )
    ORDERS[order_id] = order
    return order

def get_order_by_id(order_id: str) -> Optional[Order]:
    return ORDERS.get(order_id)

def get_all_orders() -> List[Order]:
    # Return latest first
    return sorted(list(ORDERS.values()), key=lambda o: o.created_at, reverse=True)

def update_order_status(order_id: str, new_status: str) -> Optional[Order]:
    if order_id in ORDERS:
        order = ORDERS[order_id]
        order.order_status = new_status
        order.updated_at = datetime.now(timezone.utc).isoformat()
        return order
    return None

def process_return_request(order_id: str, return_reason: str) -> Optional[Order]:
    if order_id in ORDERS:
        order = ORDERS[order_id]
        order.order_status = "RETURN_REQUESTED"
        order.return_reason = return_reason
        order.updated_at = datetime.now(timezone.utc).isoformat()
        return order
    return None
