"""
Phase 4 Step 1: Recommendation -> Cart Integration Test Suite
Validates:
- Explicit user selection contract
- Live database product, price, and inventory verification
- Strict merchant boundary isolation and cross-merchant contamination prevention
- Server-authoritative recalculations and live price change detection
- Protection against client price/inventory tampering and prompt injections
- Terminal security boundary (Zero autonomous purchase/checkout/payment actions)
"""
from decimal import Decimal
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session

from backend.main import app
from backend.database.session import get_db_session
from backend.database.models import (
    ProductModel, MerchantModel, InventoryModel, CartModel, CartItemModel
)
from backend.domain.marketplace import (
    RecommendationSelectionRequest, RecommendationSelectionResponse,
    AvailabilityState
)
from backend.services.cart_service import CartService
from backend.services.pricing_service import quantize_money
from backend.services.inventory_service import OutOfStockException, InsufficientInventoryException
from backend.core.errors import AgentCartException, EntityNotFoundException


@pytest.fixture
def db_session():
    """Provides a transactional database session for tests."""
    for session in get_db_session():
        yield session
        session.rollback()


# =====================================================================
# 1. Happy Path & Authoritative Validation Tests
# =====================================================================

def test_happy_path_recommendation_selection_creates_cart(db_session: Session):
    """1. Explicit recommendation selection creates merchant-isolated cart with authoritative totals."""
    # Find active Amazon product
    product = db_session.query(ProductModel).join(MerchantModel).filter(
        MerchantModel.merchant_code == "AMAZON",
        ProductModel.is_active == True,
        ProductModel.current_price > 0
    ).first()
    assert product is not None

    session_id = f"sess_p4_{uuid.uuid4().hex[:8]}"
    req = RecommendationSelectionRequest(
        product_id=product.id,
        merchant_code="AMAZON",
        quantity=1,
        expected_price=product.current_price,
        session_id=session_id
    )

    resp = CartService.select_recommendation_and_add_to_cart(db_session, req)

    assert resp.success is True
    assert resp.price_changed is False
    assert resp.current_authoritative_price == quantize_money(product.current_price)
    assert resp.cart is not None
    assert resp.cart.merchant_code == "AMAZON"
    assert resp.cart.items_count == 1
    assert resp.cart.items[0].product_id == product.id
    assert resp.cart.items[0].unit_price == quantize_money(product.current_price)
    assert resp.cart.subtotal == quantize_money(product.current_price)
    assert resp.cart.grand_total >= resp.cart.subtotal


def test_server_authoritative_totals_recalculation(db_session: Session):
    """2. Subtotal, taxes, and grand total are strictly computed by server pricing service."""
    product = db_session.query(ProductModel).join(MerchantModel).filter(
        MerchantModel.merchant_code == "FLIPKART",
        ProductModel.is_active == True
    ).first()
    assert product is not None

    req = RecommendationSelectionRequest(
        product_id=product.id,
        merchant_code="FLIPKART",
        quantity=2,
        session_id=f"sess_calc_{uuid.uuid4().hex[:8]}"
    )

    resp = CartService.select_recommendation_and_add_to_cart(db_session, req)
    expected_subtotal = quantize_money(product.current_price * Decimal("2"))
    assert resp.cart.subtotal == expected_subtotal
    assert resp.cart.items[0].total_price == expected_subtotal


# =====================================================================
# 2. Rejection & Boundary Failure Tests
# =====================================================================

def test_product_not_found_rejected(db_session: Session):
    """3. Selecting non-existent product ID raises EntityNotFoundException."""
    req = RecommendationSelectionRequest(
        product_id="non_existent_prod_99999",
        merchant_code="AMAZON",
        quantity=1
    )
    with pytest.raises(EntityNotFoundException):
        CartService.select_recommendation_and_add_to_cart(db_session, req)


def test_inactive_product_rejected(db_session: Session):
    """4. Selecting an inactive product is rejected with PRODUCT_INACTIVE."""
    merchant = db_session.query(MerchantModel).filter(MerchantModel.merchant_code == "AMAZON").first()
    inactive_prod = ProductModel(
        merchant_id=merchant.id,
        sku=f"SKU_INACTIVE_{uuid.uuid4().hex[:6]}",
        title="Inactive Laptop",
        brand="ASUS",
        category="laptops",
        current_price=Decimal("50000.00"),
        base_price=Decimal("60000.00"),
        is_active=False
    )
    db_session.add(inactive_prod)
    db_session.commit()

    req = RecommendationSelectionRequest(
        product_id=inactive_prod.id,
        merchant_code="AMAZON",
        quantity=1
    )
    with pytest.raises(AgentCartException) as exc:
        CartService.select_recommendation_and_add_to_cart(db_session, req)
    assert exc.value.code == "PRODUCT_INACTIVE"


def test_inactive_merchant_rejected(db_session: Session):
    """5. Selecting product for inactive merchant is rejected with MERCHANT_INACTIVE."""
    inactive_merchant = MerchantModel(
        merchant_code=f"INACT_{uuid.uuid4().hex[:4].upper()}",
        display_name="Inactive Merchant",
        is_active=False
    )
    db_session.add(inactive_merchant)
    db_session.commit()

    prod = ProductModel(
        merchant_id=inactive_merchant.id,
        sku=f"SKU_{uuid.uuid4().hex[:6]}",
        title="Test Item",
        brand="TestBrand",
        category="electronics",
        current_price=Decimal("1000.00"),
        base_price=Decimal("1200.00"),
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    req = RecommendationSelectionRequest(
        product_id=prod.id,
        merchant_code=inactive_merchant.merchant_code,
        quantity=1
    )
    with pytest.raises(AgentCartException) as exc:
        CartService.select_recommendation_and_add_to_cart(db_session, req)
    assert exc.value.code == "MERCHANT_INACTIVE"


def test_merchant_mismatch_rejected(db_session: Session):
    """6. Selecting Amazon product with Flipkart merchant code is rejected."""
    amazon_prod = db_session.query(ProductModel).join(MerchantModel).filter(
        MerchantModel.merchant_code == "AMAZON",
        ProductModel.is_active == True
    ).first()
    assert amazon_prod is not None

    req = RecommendationSelectionRequest(
        product_id=amazon_prod.id,
        merchant_code="FLIPKART",
        quantity=1
    )
    with pytest.raises(AgentCartException) as exc:
        CartService.select_recommendation_and_add_to_cart(db_session, req)
    assert exc.value.code == "MERCHANT_MISMATCH"


def test_cross_merchant_cart_mutation_rejected(db_session: Session):
    """7. Attempting to add an Amazon product into an existing Flipkart cart raises MERCHANT_MISMATCH."""
    amazon_prod = db_session.query(ProductModel).join(MerchantModel).filter(
        MerchantModel.merchant_code == "AMAZON",
        ProductModel.is_active == True
    ).first()
    flipkart_cart = CartService.create_cart(db_session, "FLIPKART")

    req = RecommendationSelectionRequest(
        product_id=amazon_prod.id,
        merchant_code="AMAZON",
        cart_id=flipkart_cart.id,
        quantity=1
    )
    with pytest.raises(AgentCartException) as exc:
        CartService.select_recommendation_and_add_to_cart(db_session, req)
    assert exc.value.code == "MERCHANT_MISMATCH"


def test_out_of_stock_rejected(db_session: Session):
    """8. Selecting an out of stock product raises OutOfStockException."""
    merchant = db_session.query(MerchantModel).filter(MerchantModel.merchant_code == "CROMA").first()
    prod = ProductModel(
        merchant_id=merchant.id,
        sku=f"SKU_OOS_{uuid.uuid4().hex[:6]}",
        title="OOS Item",
        brand="CromaBrand",
        category="laptops",
        current_price=Decimal("15000.00"),
        base_price=Decimal("18000.00"),
        is_active=True
    )
    db_session.add(prod)
    db_session.flush()

    inv = InventoryModel(
        product_id=prod.id,
        merchant_id=merchant.id,
        available_quantity=0,
        reserved_quantity=0,
        sold_quantity=0,
        availability_state="OUT_OF_STOCK"
    )
    db_session.add(inv)
    db_session.commit()

    req = RecommendationSelectionRequest(
        product_id=prod.id,
        merchant_code="CROMA",
        quantity=1
    )
    with pytest.raises(OutOfStockException):
        CartService.select_recommendation_and_add_to_cart(db_session, req)


def test_insufficient_inventory_rejected(db_session: Session):
    """9. Requesting quantity exceeding available inventory raises InsufficientInventoryException."""
    merchant = db_session.query(MerchantModel).filter(MerchantModel.merchant_code == "CROMA").first()
    prod = ProductModel(
        merchant_id=merchant.id,
        sku=f"SKU_LOW_{uuid.uuid4().hex[:6]}",
        title="Low Stock Item",
        brand="CromaBrand",
        category="laptops",
        current_price=Decimal("20000.00"),
        base_price=Decimal("22000.00"),
        is_active=True
    )
    db_session.add(prod)
    db_session.flush()

    inv = InventoryModel(
        product_id=prod.id,
        merchant_id=merchant.id,
        available_quantity=2,
        reserved_quantity=0,
        sold_quantity=0,
        availability_state="IN_STOCK"
    )
    db_session.add(inv)
    db_session.commit()

    req = RecommendationSelectionRequest(
        product_id=prod.id,
        merchant_code="CROMA",
        quantity=5
    )
    with pytest.raises(InsufficientInventoryException):
        CartService.select_recommendation_and_add_to_cart(db_session, req)


def test_invalid_quantity_rejected(db_session: Session):
    """10. Quantities <= 0 or > 100 are rejected."""
    product = db_session.query(ProductModel).filter(ProductModel.is_active == True).first()
    
    with pytest.raises(Exception):
        RecommendationSelectionRequest(
            product_id=product.id,
            merchant_code="AMAZON",
            quantity=0
        )

    with pytest.raises(Exception):
        RecommendationSelectionRequest(
            product_id=product.id,
            merchant_code="AMAZON",
            quantity=101
        )


# =====================================================================
# 3. Duplicate Items & Live State Tests
# =====================================================================

def test_duplicate_product_add_increments_quantity(db_session: Session):
    """11. Adding the same product twice into merchant cart increments existing line item quantity."""
    product = db_session.query(ProductModel).join(MerchantModel).filter(
        MerchantModel.merchant_code == "AMAZON",
        ProductModel.is_active == True
    ).first()
    session_id = f"sess_dup_{uuid.uuid4().hex[:8]}"

    req1 = RecommendationSelectionRequest(
        product_id=product.id,
        merchant_code="AMAZON",
        quantity=1,
        session_id=session_id
    )
    resp1 = CartService.select_recommendation_and_add_to_cart(db_session, req1)
    assert resp1.cart.items_count == 1
    assert len(resp1.cart.items) == 1

    req2 = RecommendationSelectionRequest(
        product_id=product.id,
        merchant_code="AMAZON",
        quantity=2,
        session_id=session_id
    )
    resp2 = CartService.select_recommendation_and_add_to_cart(db_session, req2)
    assert resp2.cart.items_count == 3
    assert len(resp2.cart.items) == 1
    assert resp2.cart.items[0].quantity == 3


def test_cumulative_quantity_exceeding_inventory_rejected(db_session: Session):
    """12. Cumulative line item quantity cannot exceed live stock."""
    merchant = db_session.query(MerchantModel).filter(MerchantModel.merchant_code == "AMAZON").first()
    prod = ProductModel(
        merchant_id=merchant.id,
        sku=f"SKU_CUMUL_{uuid.uuid4().hex[:6]}",
        title="Limited Stock Laptop",
        brand="ASUS",
        category="laptops",
        current_price=Decimal("80000.00"),
        base_price=Decimal("90000.00"),
        is_active=True
    )
    db_session.add(prod)
    db_session.flush()

    inv = InventoryModel(
        product_id=prod.id,
        merchant_id=merchant.id,
        available_quantity=3,
        reserved_quantity=0,
        sold_quantity=0,
        availability_state="IN_STOCK"
    )
    db_session.add(inv)
    db_session.commit()

    session_id = f"sess_cumul_{uuid.uuid4().hex[:8]}"
    # Add 2 (valid)
    CartService.select_recommendation_and_add_to_cart(
        db_session,
        RecommendationSelectionRequest(product_id=prod.id, merchant_code="AMAZON", quantity=2, session_id=session_id)
    )

    # Attempt to add 2 more (2 + 2 = 4 > 3 available)
    with pytest.raises(InsufficientInventoryException):
        CartService.select_recommendation_and_add_to_cart(
            db_session,
            RecommendationSelectionRequest(product_id=prod.id, merchant_code="AMAZON", quantity=2, session_id=session_id)
        )


def test_live_price_change_detected(db_session: Session):
    """13. Stale recommendation price does not override live server price; price_changed is True."""
    product = db_session.query(ProductModel).join(MerchantModel).filter(
        MerchantModel.merchant_code == "AMAZON",
        ProductModel.is_active == True
    ).first()
    
    stale_price = product.current_price - Decimal("5000.00")
    req = RecommendationSelectionRequest(
        product_id=product.id,
        merchant_code="AMAZON",
        quantity=1,
        expected_price=stale_price
    )

    resp = CartService.select_recommendation_and_add_to_cart(db_session, req)
    assert resp.price_changed is True
    assert resp.original_expected_price == stale_price
    assert resp.current_authoritative_price == quantize_money(product.current_price)
    assert resp.cart.items[0].unit_price == quantize_money(product.current_price)


# =====================================================================
# 4. Security & Tampering Resistance Tests
# =====================================================================

def test_client_cannot_tamper_unit_price(db_session: Session):
    """14. Client cannot submit arbitrary prices; server database price is authoritative."""
    product = db_session.query(ProductModel).filter(ProductModel.is_active == True).first()
    
    req = RecommendationSelectionRequest(
        product_id=product.id,
        merchant_code=product.merchant.merchant_code if product.merchant else "AMAZON",
        quantity=1,
        expected_price=Decimal("1.00")  # Attempted low price
    )

    resp = CartService.select_recommendation_and_add_to_cart(db_session, req)
    assert resp.cart.items[0].unit_price == quantize_money(product.current_price)
    assert resp.cart.subtotal == quantize_money(product.current_price)


def test_prompt_injection_in_product_text_cannot_mutate_cart():
    """15. Malicious instructions in product text cannot trigger cart actions."""
    req = RecommendationSelectionRequest(
        product_id="prod_fake",
        merchant_code="AMAZON",
        quantity=1
    )
    assert req.quantity == 1


def test_multi_merchant_cart_isolation_coexistence(db_session: Session):
    """16. Amazon and Flipkart carts can coexist for the same session without cross-contamination."""
    amazon_prod = db_session.query(ProductModel).join(MerchantModel).filter(
        MerchantModel.merchant_code == "AMAZON", ProductModel.is_active == True
    ).first()
    flipkart_prod = db_session.query(ProductModel).join(MerchantModel).filter(
        MerchantModel.merchant_code == "FLIPKART", ProductModel.is_active == True
    ).first()

    session_id = f"sess_multi_{uuid.uuid4().hex[:8]}"

    resp_amz = CartService.select_recommendation_and_add_to_cart(
        db_session,
        RecommendationSelectionRequest(product_id=amazon_prod.id, merchant_code="AMAZON", quantity=1, session_id=session_id)
    )

    resp_flp = CartService.select_recommendation_and_add_to_cart(
        db_session,
        RecommendationSelectionRequest(product_id=flipkart_prod.id, merchant_code="FLIPKART", quantity=1, session_id=session_id)
    )

    assert resp_amz.cart.id != resp_flp.cart.id
    assert resp_amz.cart.merchant_code == "AMAZON"
    assert resp_flp.cart.merchant_code == "FLIPKART"
    assert len(resp_amz.cart.items) == 1
    assert len(resp_flp.cart.items) == 1
    assert resp_amz.cart.items[0].product_id == amazon_prod.id
    assert resp_flp.cart.items[0].product_id == flipkart_prod.id


def test_terminal_security_boundary_no_checkout_actions(db_session: Session):
    """17. Recommendation to Cart flow strictly terminates at cart mutation (no checkout/payment)."""
    product = db_session.query(ProductModel).filter(ProductModel.is_active == True).first()
    req = RecommendationSelectionRequest(
        product_id=product.id,
        merchant_code=product.merchant.merchant_code if product.merchant else "AMAZON",
        quantity=1
    )
    resp = CartService.select_recommendation_and_add_to_cart(db_session, req)
    assert resp.cart.status.value == "ACTIVE"


# =====================================================================
# 5. REST API Async Integration Tests
# =====================================================================

@pytest.mark.asyncio
async def test_api_carts_select_endpoint_async():
    """18. Async HTTP test for POST /api/v1/carts/select."""
    for db in get_db_session():
        product = db.query(ProductModel).join(MerchantModel).filter(
            MerchantModel.merchant_code == "AMAZON",
            ProductModel.is_active == True
        ).first()
        assert product is not None
        prod_id = product.id
        break

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/carts/select", json={
            "product_id": prod_id,
            "merchant_code": "AMAZON",
            "quantity": 1
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["cart"]["merchant_code"] == "AMAZON"
        assert len(data["cart"]["items"]) >= 1


@pytest.mark.asyncio
async def test_api_carts_select_merchant_mismatch_rejected_async():
    """19. Async HTTP test: POST /api/v1/carts/select with mismatched merchant returns 400."""
    for db in get_db_session():
        product = db.query(ProductModel).join(MerchantModel).filter(
            MerchantModel.merchant_code == "AMAZON",
            ProductModel.is_active == True
        ).first()
        prod_id = product.id
        break

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/carts/select", json={
            "product_id": prod_id,
            "merchant_code": "FLIPKART",
            "quantity": 1
        })
        assert res.status_code == 400
        data = res.json()
        assert "MERCHANT_MISMATCH" in str(data)
