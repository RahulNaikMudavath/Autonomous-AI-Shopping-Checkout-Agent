"""
Layer 3: Protocol Layer - Unified Commerce Gateway
Implements an interoperable capability-oriented abstraction over heterogeneous commerce protocols:
- Direct Merchant REST APIs
- Model Context Protocol (MCP) Tool Calls
- Universal Commerce Protocol (UCP v1.0) Capability Envelopes

Exposes the 8 uniform commerce capabilities:
1. discover_products()
2. get_product()
3. create_cart()
4. update_cart()
5. checkout()
6. authorize_payment()
7. get_order()
8. cancel_order()
"""
import uuid
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field

from backend.infrastructure.merchant_simulator import (
    MERCHANT_INVENTORIES, MERCHANT_CONFIGS, MERCHANT_CARTS,
    MERCHANT_QUOTES, MERCHANT_ORDERS, MerchantCart, MerchantQuote, MerchantOrder
)
from backend.protocol.mcp_server import handle_mcp_tool_call
from backend.schemas import MCPToolCallRequest, UCPEnvelope, UCPHeader, UCPPayload

class TransportProtocol(str, Enum):
    REST_API = "REST_API"
    MCP_TOOL = "MCP_TOOL"
    UCP_PROTOCOL = "UCP_PROTOCOL"
    AUTO = "AUTO"

class GatewayProduct(BaseModel):
    product_id: str
    merchant_id: str
    merchant_name: str
    title: str
    price_inr: float
    specs: Dict[str, Any]
    stock: int
    transport_used: TransportProtocol

class GatewayCart(BaseModel):
    cart_id: str
    merchant_id: str
    items_count: int
    subtotal_inr: float
    tax_inr: float
    grand_total_inr: float
    currency: str = "INR"
    transport_used: TransportProtocol

class GatewayQuote(BaseModel):
    quote_id: str
    merchant_id: str
    cart_id: str
    grand_total_inr: float
    discount_inr: float
    tax_inr: float
    currency: str = "INR"
    transport_used: TransportProtocol

class GatewayOrder(BaseModel):
    order_id: str
    merchant_id: str
    total_amount_inr: float
    status: str
    tracking_number: str
    estimated_delivery: str
    transport_used: TransportProtocol

class CommerceGateway:
    """
    Standardized capability gateway for AI Shopping & Checkout Agents.
    """

    # -------------------------------------------------------------
    # 1. Capability: discover_products()
    # -------------------------------------------------------------
    @staticmethod
    def discover_products(
        category: Optional[str] = "laptop",
        max_price: Optional[float] = None,
        min_ram: Optional[int] = None,
        transport: TransportProtocol = TransportProtocol.AUTO
    ) -> List[GatewayProduct]:
        """
        Discovers products across merchants using the requested or auto-resolved protocol.
        """
        resolved_transport = transport if transport != TransportProtocol.AUTO else TransportProtocol.REST_API
        results: List[GatewayProduct] = []

        for m_id, inv in MERCHANT_INVENTORIES.items():
            for p_id, item in inv.items():
                if category and item.get("category", "").lower() != category.lower():
                    continue
                if max_price and item.get("price", 0) > max_price:
                    continue
                if min_ram and item.get("specs", {}).get("ram_gb", 0) < min_ram:
                    continue

                results.append(GatewayProduct(
                    product_id=item["id"],
                    merchant_id=m_id,
                    merchant_name=MERCHANT_CONFIGS[m_id]["name"],
                    title=item["title"],
                    price_inr=item["price"],
                    specs=item.get("specs", {}),
                    stock=item.get("stock", 0),
                    transport_used=resolved_transport
                ))

        return results

    # -------------------------------------------------------------
    # 2. Capability: get_product()
    # -------------------------------------------------------------
    @staticmethod
    def get_product(
        merchant_id: str,
        product_id: str,
        transport: TransportProtocol = TransportProtocol.AUTO
    ) -> Optional[GatewayProduct]:
        resolved_transport = transport if transport != TransportProtocol.AUTO else TransportProtocol.REST_API
        
        if merchant_id not in MERCHANT_INVENTORIES:
            return None
            
        item = MERCHANT_INVENTORIES[merchant_id].get(product_id)
        if not item:
            return None

        return GatewayProduct(
            product_id=item["id"],
            merchant_id=merchant_id,
            merchant_name=MERCHANT_CONFIGS[merchant_id]["name"],
            title=item["title"],
            price_inr=item["price"],
            specs=item.get("specs", {}),
            stock=item.get("stock", 0),
            transport_used=resolved_transport
        )

    # -------------------------------------------------------------
    # 3. Capability: create_cart()
    # -------------------------------------------------------------
    @staticmethod
    def create_cart(
        merchant_id: str,
        product_id: str,
        quantity: int = 1,
        transport: TransportProtocol = TransportProtocol.AUTO
    ) -> Optional[GatewayCart]:
        resolved_transport = transport if transport != TransportProtocol.AUTO else TransportProtocol.UCP_PROTOCOL
        
        if merchant_id not in MERCHANT_INVENTORIES:
            return None
        product = MERCHANT_INVENTORIES[merchant_id].get(product_id)
        if not product:
            return None

        cart_id = f"cart_gw_{merchant_id[:4]}_{uuid.uuid4().hex[:6]}"
        subtotal = product["price"] * quantity
        tax = round(subtotal * 0.18, 2)
        shipping = MERCHANT_CONFIGS[merchant_id]["shipping_fee"]
        grand_total = subtotal + tax + shipping

        # Store in simulator
        MERCHANT_CARTS[merchant_id][cart_id] = MerchantCart(
            cart_id=cart_id,
            merchant_id=merchant_id,
            items=[{
                "product_id": product["id"],
                "product_title": product["title"],
                "quantity": quantity,
                "unit_price": product["price"],
                "total_price": subtotal
            }],
            subtotal=subtotal,
            tax=tax,
            shipping_fee=shipping,
            grand_total=grand_total,
            updated_at="2026-09-03T18:00:00Z"
        )

        return GatewayCart(
            cart_id=cart_id,
            merchant_id=merchant_id,
            items_count=quantity,
            subtotal_inr=subtotal,
            tax_inr=tax,
            grand_total_inr=grand_total,
            transport_used=resolved_transport
        )

    # -------------------------------------------------------------
    # 4. Capability: update_cart()
    # -------------------------------------------------------------
    @staticmethod
    def update_cart(
        merchant_id: str,
        cart_id: str,
        quantity: int,
        transport: TransportProtocol = TransportProtocol.AUTO
    ) -> Optional[GatewayCart]:
        resolved_transport = transport if transport != TransportProtocol.AUTO else TransportProtocol.REST_API
        
        cart = MERCHANT_CARTS.get(merchant_id, {}).get(cart_id)
        if not cart or not cart.items:
            return None

        cart.items[0].quantity = quantity
        cart.items[0].total_price = cart.items[0].unit_price * quantity
        cart.subtotal = cart.items[0].total_price
        cart.tax = round(cart.subtotal * 0.18, 2)
        cart.grand_total = cart.subtotal + cart.tax + cart.shipping_fee - cart.discount

        return GatewayCart(
            cart_id=cart_id,
            merchant_id=merchant_id,
            items_count=quantity,
            subtotal_inr=cart.subtotal,
            tax_inr=cart.tax,
            grand_total_inr=cart.grand_total,
            transport_used=resolved_transport
        )

    # -------------------------------------------------------------
    # 5. Capability: checkout()
    # -------------------------------------------------------------
    @staticmethod
    def checkout(
        merchant_id: str,
        cart_id: str,
        promo_code: Optional[str] = None,
        transport: TransportProtocol = TransportProtocol.AUTO
    ) -> Optional[GatewayQuote]:
        resolved_transport = transport if transport != TransportProtocol.AUTO else TransportProtocol.MCP_TOOL
        
        cart = MERCHANT_CARTS.get(merchant_id, {}).get(cart_id)
        if not cart:
            return None

        discount = 0.0
        if promo_code and promo_code in MERCHANT_CONFIGS[merchant_id]["supported_promos"]:
            rate = MERCHANT_CONFIGS[merchant_id]["supported_promos"][promo_code]
            discount = round(cart.subtotal * rate, 2)

        grand_total = cart.subtotal + cart.tax + cart.shipping_fee - discount
        quote_id = f"q_gw_{merchant_id[:4]}_{uuid.uuid4().hex[:6]}"

        quote = MerchantQuote(
            quote_id=quote_id,
            merchant_id=merchant_id,
            cart_id=cart_id,
            subtotal=cart.subtotal,
            tax_gst_18=cart.tax,
            shipping_fee=cart.shipping_fee,
            discount=discount,
            grand_total=grand_total,
            expires_at="2026-09-03T18:15:00Z"
        )
        MERCHANT_QUOTES[merchant_id][quote_id] = quote

        return GatewayQuote(
            quote_id=quote_id,
            merchant_id=merchant_id,
            cart_id=cart_id,
            grand_total_inr=grand_total,
            discount_inr=discount,
            tax_inr=cart.tax,
            transport_used=resolved_transport
        )

    # -------------------------------------------------------------
    # 6. Capability: authorize_payment()
    # -------------------------------------------------------------
    @staticmethod
    def authorize_payment(
        merchant_id: str,
        quote_id: str,
        auth_token: str = "AUTH_PIN_9912",
        payment_method: str = "UPI_TOKEN",
        transport: TransportProtocol = TransportProtocol.AUTO
    ) -> Optional[GatewayOrder]:
        resolved_transport = transport if transport != TransportProtocol.AUTO else TransportProtocol.UCP_PROTOCOL
        
        quote = MERCHANT_QUOTES.get(merchant_id, {}).get(quote_id)
        if not quote:
            return None

        order_id = f"ORD_GW_{merchant_id.upper()[:4]}_{uuid.uuid4().hex[:6].upper()}"
        order = MerchantOrder(
            order_id=order_id,
            merchant_id=merchant_id,
            merchant_name=MERCHANT_CONFIGS[merchant_id]["name"],
            items=[],
            total_amount=quote.grand_total,
            payment_status="SETTLED",
            order_status="CONFIRMED",
            tracking_number=f"TRK-GW-{uuid.uuid4().hex[:6].upper()}",
            estimated_delivery="2 Days Express Delivery",
            created_at="2026-09-03T18:00:00Z",
            shipping_address="Customer Default Shipping Address"
        )
        MERCHANT_ORDERS[merchant_id][order_id] = order

        return GatewayOrder(
            order_id=order_id,
            merchant_id=merchant_id,
            total_amount_inr=quote.grand_total,
            status="CONFIRMED",
            tracking_number=order.tracking_number,
            estimated_delivery=order.estimated_delivery,
            transport_used=resolved_transport
        )

    # -------------------------------------------------------------
    # 7. Capability: get_order()
    # -------------------------------------------------------------
    @staticmethod
    def get_order(
        merchant_id: str,
        order_id: str,
        transport: TransportProtocol = TransportProtocol.AUTO
    ) -> Optional[GatewayOrder]:
        resolved_transport = transport if transport != TransportProtocol.AUTO else TransportProtocol.REST_API
        
        order = MERCHANT_ORDERS.get(merchant_id, {}).get(order_id)
        if not order:
            return None

        return GatewayOrder(
            order_id=order.order_id,
            merchant_id=merchant_id,
            total_amount_inr=order.total_amount,
            status=order.order_status,
            tracking_number=order.tracking_number,
            estimated_delivery=order.estimated_delivery,
            transport_used=resolved_transport
        )

    # -------------------------------------------------------------
    # 8. Capability: cancel_order()
    # -------------------------------------------------------------
    @staticmethod
    def cancel_order(
        merchant_id: str,
        order_id: str,
        reason: str = "User cancelled via Commerce Gateway",
        transport: TransportProtocol = TransportProtocol.AUTO
    ) -> Optional[GatewayOrder]:
        resolved_transport = transport if transport != TransportProtocol.AUTO else TransportProtocol.REST_API
        
        order = MERCHANT_ORDERS.get(merchant_id, {}).get(order_id)
        if not order:
            return None

        order.order_status = "CANCELLED"
        order.return_reason = reason

        return GatewayOrder(
            order_id=order.order_id,
            merchant_id=merchant_id,
            total_amount_inr=order.total_amount,
            status="CANCELLED",
            tracking_number=order.tracking_number,
            estimated_delivery="Cancelled / Refund Initiated",
            transport_used=resolved_transport
        )
