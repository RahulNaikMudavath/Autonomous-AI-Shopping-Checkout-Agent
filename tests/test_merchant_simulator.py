"""
Test Suite for 4. Merchant Simulator (Mini Marketplace Backend)
Tests all 8 standard commerce endpoints across merchant-a, merchant-b, merchant-c, and merchant-d.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_all_8_merchant_simulator_endpoints_merchant_a():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        merchant_id = "merchant-a"

        # 1. GET /products
        res1 = await ac.get(f"/api/merchants/{merchant_id}/products")
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["merchant_id"] == merchant_id
        assert data1["count"] >= 1
        product_id = data1["products"][0]["id"]

        # 2. GET /products/{id}
        res2 = await ac.get(f"/api/merchants/{merchant_id}/products/{product_id}")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["product"]["id"] == product_id

        # 3. POST /cart
        res3 = await ac.post(f"/api/merchants/{merchant_id}/cart", json={
            "product_id": product_id,
            "quantity": 1
        })
        assert res3.status_code == 200
        cart_data = res3.json()
        cart_id = cart_data["cart_id"]
        assert len(cart_data["items"]) == 1
        assert cart_data["items"][0]["quantity"] == 1

        # 4. PATCH /cart/{id}
        res4 = await ac.patch(f"/api/merchants/{merchant_id}/cart/{cart_id}", json={
            "quantity": 2
        })
        assert res4.status_code == 200
        cart_data_patched = res4.json()
        assert cart_data_patched["items"][0]["quantity"] == 2

        # 5. POST /checkout
        res5 = await ac.post(f"/api/merchants/{merchant_id}/checkout", json={
            "cart_id": cart_id,
            "promo_code": "AI_DEVELOPER_5OFF"
        })
        assert res5.status_code == 200
        quote_data = res5.json()
        quote_id = quote_data["quote_id"]
        assert quote_data["discount"] > 0
        assert quote_data["grand_total"] > 0

        # 6. POST /payment
        res6 = await ac.post(f"/api/merchants/{merchant_id}/payment", json={
            "quote_id": quote_id,
            "payment_method": "UPI_TOKEN_4829",
            "auth_token": "AUTH_PIN_9912"
        })
        assert res6.status_code == 200
        order_data = res6.json()
        order_id = order_data["order_id"]
        assert order_data["payment_status"] == "SETTLED"
        assert order_data["order_status"] == "CONFIRMED"

        # 7. GET /orders/{id}
        res7 = await ac.get(f"/api/merchants/{merchant_id}/orders/{order_id}")
        assert res7.status_code == 200
        fetched_order = res7.json()
        assert fetched_order["order_id"] == order_id
        assert fetched_order["tracking_number"].startswith("TRK-")

        # 8. POST /returns/{order_id}
        res8 = await ac.post(f"/api/merchants/{merchant_id}/returns/{order_id}", json={
            "reason": "Upgrading to 64GB configuration"
        })
        assert res8.status_code == 200
        returned_order = res8.json()
        assert returned_order["order_status"] == "RETURN_REQUESTED"
        assert returned_order["return_reason"] == "Upgrading to 64GB configuration"

@pytest.mark.asyncio
async def test_merchant_b_c_d_catalogs_and_quotes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for m_id in ["merchant-b", "merchant-c", "merchant-d"]:
            res = await ac.get(f"/api/merchants/{m_id}/products")
            assert res.status_code == 200
            data = res.json()
            assert data["count"] >= 1
            
            p_id = data["products"][0]["id"]
            # Cart & quote flow
            c_res = await ac.post(f"/api/merchants/{m_id}/cart", json={"product_id": p_id, "quantity": 1})
            assert c_res.status_code == 200
            cart_id = c_res.json()["cart_id"]

            q_res = await ac.post(f"/api/merchants/{m_id}/checkout", json={"cart_id": cart_id})
            assert q_res.status_code == 200
            assert q_res.json()["grand_total"] > 0
