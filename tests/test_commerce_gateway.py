"""
Test Suite for 5. Protocol Layer (Commerce Gateway & 8 Unified Capabilities)
Validates protocol transparency across REST, MCP, and UCP capability envelopes.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.protocol.commerce_gateway import CommerceGateway, TransportProtocol

def test_gateway_python_capabilities():
    # 1. discover_products()
    products = CommerceGateway.discover_products(
        category="laptop",
        max_price=120000,
        min_ram=32,
        transport=TransportProtocol.AUTO
    )
    assert len(products) >= 1
    assert all(p.price_inr <= 120000 for p in products)
    assert any("ROG Strix" in p.title or "Predator Helios" in p.title for p in products)

    # 2. get_product()
    prod = CommerceGateway.get_product("merchant-a", "prod_laptop_b_rog", TransportProtocol.REST_API)
    assert prod is not None
    assert prod.merchant_id == "merchant-a"
    assert prod.transport_used == TransportProtocol.REST_API

    # 3. create_cart()
    cart = CommerceGateway.create_cart("merchant-a", "prod_laptop_b_rog", 1, TransportProtocol.UCP_PROTOCOL)
    assert cart is not None
    assert cart.grand_total_inr > 0
    assert cart.transport_used == TransportProtocol.UCP_PROTOCOL

    # 4. update_cart()
    cart_updated = CommerceGateway.update_cart("merchant-a", cart.cart_id, 2, TransportProtocol.REST_API)
    assert cart_updated is not None
    assert cart_updated.items_count == 2

    # 5. checkout()
    quote = CommerceGateway.checkout("merchant-a", cart.cart_id, "AI_DEVELOPER_5OFF", TransportProtocol.MCP_TOOL)
    assert quote is not None
    assert quote.discount_inr > 0
    assert quote.transport_used == TransportProtocol.MCP_TOOL

    # 6. authorize_payment()
    order = CommerceGateway.authorize_payment("merchant-a", quote.quote_id, "AUTH_PIN_9912", "UPI_TOKEN", TransportProtocol.UCP_PROTOCOL)
    assert order is not None
    assert order.status == "CONFIRMED"
    assert order.tracking_number.startswith("TRK-GW-")

    # 7. get_order()
    fetched_order = CommerceGateway.get_order("merchant-a", order.order_id, TransportProtocol.REST_API)
    assert fetched_order is not None
    assert fetched_order.order_id == order.order_id

    # 8. cancel_order()
    cancelled = CommerceGateway.cancel_order("merchant-a", order.order_id, "Customer requested cancellation")
    assert cancelled is not None
    assert cancelled.status == "CANCELLED"

@pytest.mark.asyncio
async def test_gateway_rest_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Discover
        res1 = await ac.post("/api/gateway/discover-products", json={
            "category": "laptop",
            "max_price": 120000
        })
        assert res1.status_code == 200
        items = res1.json()
        assert len(items) >= 1

        # 2. Get Product
        res2 = await ac.get("/api/gateway/product/merchant-a/prod_laptop_b_rog")
        assert res2.status_code == 200
        assert res2.json()["merchant_id"] == "merchant-a"

        # 3. Create Cart
        res3 = await ac.post("/api/gateway/cart/create", json={
            "merchant_id": "merchant-a",
            "product_id": "prod_laptop_b_rog",
            "quantity": 1
        })
        assert res3.status_code == 200
        cart_id = res3.json()["cart_id"]

        # 4. Checkout Quote
        res4 = await ac.post("/api/gateway/checkout", json={
            "merchant_id": "merchant-a",
            "cart_id": cart_id,
            "promo_code": "AI_DEVELOPER_5OFF"
        })
        assert res4.status_code == 200
        quote_id = res4.json()["quote_id"]

        # 5. Authorize Payment
        res5 = await ac.post("/api/gateway/payment/authorize", json={
            "merchant_id": "merchant-a",
            "quote_id": quote_id,
            "auth_token": "PIN_1234"
        })
        assert res5.status_code == 200
        order_id = res5.json()["order_id"]

        # 6. Cancel Order
        res6 = await ac.post("/api/gateway/orders/cancel", json={
            "merchant_id": "merchant-a",
            "order_id": order_id,
            "reason": "Test cancel"
        })
        assert res6.status_code == 200
        assert res6.json()["status"] == "CANCELLED"
