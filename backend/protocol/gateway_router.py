"""
Layer 3: Protocol Layer - Gateway Router Endpoints
Exposes the 8 uniform commerce capabilities over HTTP:
- POST  /api/gateway/discover-products
- GET   /api/gateway/product/{merchant_id}/{product_id}
- POST  /api/gateway/cart/create
- PATCH /api/gateway/cart/update
- POST  /api/gateway/checkout
- POST  /api/gateway/payment/authorize
- GET   /api/gateway/orders/{merchant_id}/{order_id}
- POST  /api/gateway/orders/cancel
"""
from fastapi import APIRouter, HTTPException, Query, Body, Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from backend.protocol.commerce_gateway import (
    CommerceGateway, TransportProtocol, GatewayProduct, GatewayCart,
    GatewayQuote, GatewayOrder
)

gateway_router = APIRouter(prefix="/api/gateway", tags=["Commerce Gateway Capabilities"])

class DiscoverPayload(BaseModel):
    category: Optional[str] = "laptop"
    max_price: Optional[float] = None
    min_ram: Optional[int] = None
    transport: Optional[TransportProtocol] = TransportProtocol.AUTO

class CreateCartPayload(BaseModel):
    merchant_id: str
    product_id: str
    quantity: int = 1
    transport: Optional[TransportProtocol] = TransportProtocol.AUTO

class UpdateCartPayload(BaseModel):
    merchant_id: str
    cart_id: str
    quantity: int
    transport: Optional[TransportProtocol] = TransportProtocol.AUTO

class CheckoutPayload(BaseModel):
    merchant_id: str
    cart_id: str
    promo_code: Optional[str] = None
    transport: Optional[TransportProtocol] = TransportProtocol.AUTO

class AuthorizePaymentPayload(BaseModel):
    merchant_id: str
    quote_id: str
    auth_token: str = "AUTH_PIN_9912"
    payment_method: str = "UPI_TOKEN"
    transport: Optional[TransportProtocol] = TransportProtocol.AUTO

class CancelOrderPayload(BaseModel):
    merchant_id: str
    order_id: str
    reason: Optional[str] = "User requested cancellation"
    transport: Optional[TransportProtocol] = TransportProtocol.AUTO

# -------------------------------------------------------------
# 1. POST /api/gateway/discover-products
# -------------------------------------------------------------
@gateway_router.post("/discover-products", response_model=List[GatewayProduct])
async def gateway_discover_products(payload: DiscoverPayload):
    return CommerceGateway.discover_products(
        category=payload.category,
        max_price=payload.max_price,
        min_ram=payload.min_ram,
        transport=payload.transport or TransportProtocol.AUTO
    )

# -------------------------------------------------------------
# 2. GET /api/gateway/product/{merchant_id}/{product_id}
# -------------------------------------------------------------
@gateway_router.get("/product/{merchant_id}/{product_id}", response_model=GatewayProduct)
async def gateway_get_product(
    merchant_id: str = Path(...),
    product_id: str = Path(...),
    transport: TransportProtocol = Query(TransportProtocol.AUTO)
):
    product = CommerceGateway.get_product(merchant_id, product_id, transport)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found via Commerce Gateway")
    return product

# -------------------------------------------------------------
# 3. POST /api/gateway/cart/create
# -------------------------------------------------------------
@gateway_router.post("/cart/create", response_model=GatewayCart)
async def gateway_create_cart(payload: CreateCartPayload):
    cart = CommerceGateway.create_cart(
        merchant_id=payload.merchant_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        transport=payload.transport or TransportProtocol.AUTO
    )
    if not cart:
        raise HTTPException(status_code=400, detail="Unable to create cart via Commerce Gateway")
    return cart

# -------------------------------------------------------------
# 4. PATCH /api/gateway/cart/update
# -------------------------------------------------------------
@gateway_router.patch("/cart/update", response_model=GatewayCart)
async def gateway_update_cart(payload: UpdateCartPayload):
    cart = CommerceGateway.update_cart(
        merchant_id=payload.merchant_id,
        cart_id=payload.cart_id,
        quantity=payload.quantity,
        transport=payload.transport or TransportProtocol.AUTO
    )
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found or update failed")
    return cart

# -------------------------------------------------------------
# 5. POST /api/gateway/checkout
# -------------------------------------------------------------
@gateway_router.post("/checkout", response_model=GatewayQuote)
async def gateway_checkout(payload: CheckoutPayload):
    quote = CommerceGateway.checkout(
        merchant_id=payload.merchant_id,
        cart_id=payload.cart_id,
        promo_code=payload.promo_code,
        transport=payload.transport or TransportProtocol.AUTO
    )
    if not quote:
        raise HTTPException(status_code=400, detail="Checkout failed at Commerce Gateway")
    return quote

# -------------------------------------------------------------
# 6. POST /api/gateway/payment/authorize
# -------------------------------------------------------------
@gateway_router.post("/payment/authorize", response_model=GatewayOrder)
async def gateway_authorize_payment(payload: AuthorizePaymentPayload):
    order = CommerceGateway.authorize_payment(
        merchant_id=payload.merchant_id,
        quote_id=payload.quote_id,
        auth_token=payload.auth_token,
        payment_method=payload.payment_method,
        transport=payload.transport or TransportProtocol.AUTO
    )
    if not order:
        raise HTTPException(status_code=400, detail="Payment authorization failed")
    return order

# -------------------------------------------------------------
# 7. GET /api/gateway/orders/{merchant_id}/{order_id}
# -------------------------------------------------------------
@gateway_router.get("/orders/{merchant_id}/{order_id}", response_model=GatewayOrder)
async def gateway_get_order(
    merchant_id: str = Path(...),
    order_id: str = Path(...),
    transport: TransportProtocol = Query(TransportProtocol.AUTO)
):
    order = CommerceGateway.get_order(merchant_id, order_id, transport)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found via Commerce Gateway")
    return order

# -------------------------------------------------------------
# 8. POST /api/gateway/orders/cancel
# -------------------------------------------------------------
@gateway_router.post("/orders/cancel", response_model=GatewayOrder)
async def gateway_cancel_order(payload: CancelOrderPayload):
    order = CommerceGateway.cancel_order(
        merchant_id=payload.merchant_id,
        order_id=payload.order_id,
        reason=payload.reason or "User cancelled via Commerce Gateway",
        transport=payload.transport or TransportProtocol.AUTO
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found for cancellation")
    return order
