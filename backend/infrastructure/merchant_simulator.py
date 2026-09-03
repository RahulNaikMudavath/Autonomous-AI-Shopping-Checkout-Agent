"""
Layer 4: Commerce Infrastructure - Standalone Merchant Simulator
Implements a stateful mini marketplace backend with 4 distinct merchant instances:
- merchant-a (TechHub India)
- merchant-b (ElectroBazaar)
- merchant-c (OmniStore Online)
- merchant-d (ProHardware Direct)

Each merchant exposes the 8 standard commerce REST endpoints:
1. GET   /api/merchants/{merchant_id}/products
2. GET   /api/merchants/{merchant_id}/products/{id}
3. POST  /api/merchants/{merchant_id}/cart
4. PATCH /api/merchants/{merchant_id}/cart/{id}
5. POST  /api/merchants/{merchant_id}/checkout
6. POST  /api/merchants/{merchant_id}/payment
7. GET   /api/merchants/{merchant_id}/orders/{id}
8. POST  /api/merchants/{merchant_id}/returns
"""
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field

from backend.schemas import Product, ProductSpecs

merchant_sim_router = APIRouter(prefix="/api/merchants", tags=["Merchant Simulator API"])

# Schemas for Merchant API
class MerchantCartItem(BaseModel):
    product_id: str
    product_title: str
    quantity: int = 1
    unit_price: float
    total_price: float

class MerchantCart(BaseModel):
    cart_id: str
    merchant_id: str
    items: List[MerchantCartItem] = []
    subtotal: float = 0.0
    tax: float = 0.0
    shipping_fee: float = 0.0
    discount: float = 0.0
    grand_total: float = 0.0
    currency: str = "INR"
    updated_at: str

class AddCartPayload(BaseModel):
    product_id: str
    quantity: int = 1

class PatchCartPayload(BaseModel):
    quantity: int

class CheckoutPayload(BaseModel):
    cart_id: str
    shipping_address: Optional[str] = "Rahul N., Flat 402, HighTech Tech Park, Bangalore 560100"
    promo_code: Optional[str] = None

class MerchantQuote(BaseModel):
    quote_id: str
    merchant_id: str
    cart_id: str
    subtotal: float
    tax_gst_18: float
    shipping_fee: float
    discount: float
    grand_total: float
    currency: str = "INR"
    payment_methods_accepted: List[str] = ["UPI_TOKEN", "SAVED_CARD_VISA", "ESCROW"]
    expires_at: str

class PaymentPayload(BaseModel):
    quote_id: str
    payment_method: str = "UPI_TOKEN_4829"
    auth_token: str = "AUTH_PIN_TOKEN_9912"
    shipping_address: Optional[str] = "Rahul N., Flat 402, HighTech Tech Park, Bangalore 560100"

class MerchantOrder(BaseModel):
    order_id: str
    merchant_id: str
    merchant_name: str
    items: List[MerchantCartItem]
    total_amount: float
    currency: str = "INR"
    payment_status: str = "SETTLED"
    order_status: str = "CONFIRMED"  # CONFIRMED, PROCESSING, SHIPPED, DELIVERED, RETURN_REQUESTED, RETURNED
    tracking_number: str
    estimated_delivery: str
    created_at: str
    shipping_address: str
    return_reason: Optional[str] = None

class ReturnPayload(BaseModel):
    reason: str

# In-Memory State for each merchant
MERCHANT_CONFIGS = {
    "merchant-a": {
        "name": "TechHub India",
        "domain": "techhub.in",
        "reputation": 4.9,
        "shipping_fee": 0.0,
        "delivery_days": 2,
        "supported_promos": {"AI_DEVELOPER_5OFF": 0.05, "TECH_HUB_FREE": 0.0}
    },
    "merchant-b": {
        "name": "ElectroBazaar",
        "domain": "electrobazaar.co.in",
        "reputation": 4.7,
        "shipping_fee": 0.0,
        "delivery_days": 3,
        "supported_promos": {"SUMMER_TECH_10": 0.10}
    },
    "merchant-c": {
        "name": "OmniStore Online",
        "domain": "omnistore.in",
        "reputation": 4.6,
        "shipping_fee": 499.0,
        "delivery_days": 4,
        "supported_promos": {"EXTRA_WARRANTY": 0.0}
    },
    "merchant-d": {
        "name": "ProHardware Direct",
        "domain": "prohardware.com",
        "reputation": 4.8,
        "shipping_fee": 0.0,
        "delivery_days": 2,
        "supported_promos": {"ENTERPRISE_DEV_BUNDLE": 0.08}
    }
}

# Merchant-specific Catalogs
MERCHANT_INVENTORIES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "merchant-a": {
        "prod_laptop_b_rog": {
            "id": "prod_laptop_b_rog",
            "title": "ASUS ROG Strix G16 (2025) AI Workstation",
            "category": "laptop",
            "brand": "ASUS",
            "price": 109999.0,
            "original_price": 129999.0,
            "stock": 18,
            "specs": {
                "gpu": "NVIDIA GeForce RTX 4070 (140W TGP)",
                "gpu_vram_gb": 8,
                "ram_gb": 32,
                "ssd_gb": 1024,
                "cpu": "Intel Core i7-14650HX",
                "battery_wh": 90,
                "battery_life_hours": 8.5,
                "display": "16\" QHD+ 240Hz ROG Nebula"
            }
        },
        "prod_laptop_macbook_pro_m3": {
            "id": "prod_laptop_macbook_pro_m3",
            "title": "Apple MacBook Pro 14 (M3 Pro, 18GB, 512GB)",
            "category": "laptop",
            "brand": "Apple",
            "price": 189900.0,
            "original_price": 199900.0,
            "stock": 10,
            "specs": {
                "gpu": "Apple 14-core GPU",
                "gpu_vram_gb": 18,
                "ram_gb": 18,
                "ssd_gb": 512,
                "cpu": "Apple M3 Pro",
                "battery_wh": 70,
                "battery_life_hours": 17.0,
                "display": "14.2\" Liquid Retina XDR"
            }
        }
    },
    "merchant-b": {
        "prod_laptop_a_helios": {
            "id": "prod_laptop_a_helios",
            "title": "Acer Predator Helios Neo 16 AI ML Edition",
            "category": "laptop",
            "brand": "Acer",
            "price": 99999.0,
            "original_price": 119999.0,
            "stock": 24,
            "specs": {
                "gpu": "NVIDIA GeForce RTX 4060 (140W TGP)",
                "gpu_vram_gb": 8,
                "ram_gb": 32,
                "ssd_gb": 1024,
                "cpu": "Intel Core i7-14700HX",
                "battery_wh": 76,
                "battery_life_hours": 6.5,
                "display": "16\" WQXGA 165Hz IPS"
            }
        },
        "prod_laptop_asus_tuf_budget": {
            "id": "prod_laptop_asus_tuf_budget",
            "title": "ASUS TUF Gaming A15 AI Dev Starter",
            "category": "laptop",
            "brand": "ASUS",
            "price": 74999.0,
            "original_price": 89999.0,
            "stock": 30,
            "specs": {
                "gpu": "NVIDIA GeForce RTX 4050 (105W TGP)",
                "gpu_vram_gb": 6,
                "ram_gb": 16,
                "ssd_gb": 512,
                "cpu": "AMD Ryzen 7 7735HS",
                "battery_wh": 90,
                "battery_life_hours": 9.0,
                "display": "15.6\" FHD 144Hz"
            }
        }
    },
    "merchant-c": {
        "prod_laptop_lenovo_legion": {
            "id": "prod_laptop_lenovo_legion",
            "title": "Lenovo Legion Pro 5i Gen 9 AI Workstation",
            "category": "laptop",
            "brand": "Lenovo",
            "price": 114999.0,
            "original_price": 132000.0,
            "stock": 12,
            "specs": {
                "gpu": "NVIDIA GeForce RTX 4070 (140W TGP)",
                "gpu_vram_gb": 8,
                "ram_gb": 32,
                "ssd_gb": 1024,
                "cpu": "AMD Ryzen 7 8845HS",
                "battery_wh": 80,
                "battery_life_hours": 7.8,
                "display": "16\" WQXGA 165Hz 500 nits"
            }
        }
    },
    "merchant-d": {
        "prod_laptop_c_alienware": {
            "id": "prod_laptop_c_alienware",
            "title": "Dell G16 / Alienware ML Pro Max 64GB",
            "category": "laptop",
            "brand": "Dell",
            "price": 117999.0,
            "original_price": 134999.0,
            "stock": 8,
            "specs": {
                "gpu": "NVIDIA GeForce RTX 4070 (140W TGP)",
                "gpu_vram_gb": 8,
                "ram_gb": 64,
                "ssd_gb": 2048,
                "cpu": "Intel Core i9-13900HX",
                "battery_wh": 86,
                "battery_life_hours": 7.0,
                "display": "16\" QHD+ 240Hz G-SYNC"
            }
        }
    }
}

# In-Memory Stateful Stores per Merchant
MERCHANT_CARTS: Dict[str, Dict[str, MerchantCart]] = {
    "merchant-a": {}, "merchant-b": {}, "merchant-c": {}, "merchant-d": {}
}
MERCHANT_QUOTES: Dict[str, Dict[str, MerchantQuote]] = {
    "merchant-a": {}, "merchant-b": {}, "merchant-c": {}, "merchant-d": {}
}
MERCHANT_ORDERS: Dict[str, Dict[str, MerchantOrder]] = {
    "merchant-a": {}, "merchant-b": {}, "merchant-c": {}, "merchant-d": {}
}

def _validate_merchant_id(merchant_id: str):
    if merchant_id not in MERCHANT_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Merchant '{merchant_id}' not found. Valid: {list(MERCHANT_CONFIGS.keys())}")

# -------------------------------------------------------------
# 1. GET /api/merchants/{merchant_id}/products
# -------------------------------------------------------------
@merchant_sim_router.get("/{merchant_id}/products")
async def list_merchant_products(merchant_id: str = Path(...), category: Optional[str] = None):
    """1. GET /products — Retrieve catalog for specified merchant simulator."""
    _validate_merchant_id(merchant_id)
    items = list(MERCHANT_INVENTORIES[merchant_id].values())
    if category:
        items = [i for i in items if i.get("category", "").lower() == category.lower()]
    return {
        "merchant_id": merchant_id,
        "merchant_name": MERCHANT_CONFIGS[merchant_id]["name"],
        "count": len(items),
        "products": items
    }

# -------------------------------------------------------------
# 2. GET /api/merchants/{merchant_id}/products/{id}
# -------------------------------------------------------------
@merchant_sim_router.get("/{merchant_id}/products/{product_id}")
async def get_merchant_product(merchant_id: str = Path(...), product_id: str = Path(...)):
    """2. GET /products/{id} — Retrieve detailed product specs & stock status."""
    _validate_merchant_id(merchant_id)
    product = MERCHANT_INVENTORIES[merchant_id].get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found at {merchant_id}")
    return {
        "merchant_id": merchant_id,
        "merchant_name": MERCHANT_CONFIGS[merchant_id]["name"],
        "product": product
    }

# -------------------------------------------------------------
# 3. POST /api/merchants/{merchant_id}/cart
# -------------------------------------------------------------
@merchant_sim_router.post("/{merchant_id}/cart", response_model=MerchantCart)
async def create_or_add_merchant_cart(merchant_id: str = Path(...), payload: AddCartPayload = Body(...)):
    """3. POST /cart — Add an item to merchant-specific shopping cart."""
    _validate_merchant_id(merchant_id)
    product = MERCHANT_INVENTORIES[merchant_id].get(payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{payload.product_id}' not found at {merchant_id}")

    cart_id = f"cart_{merchant_id}_{uuid.uuid4().hex[:6]}"
    subtotal = product["price"] * payload.quantity
    shipping = MERCHANT_CONFIGS[merchant_id]["shipping_fee"]
    tax = round(subtotal * 0.18, 2)
    grand_total = subtotal + tax + shipping

    cart = MerchantCart(
        cart_id=cart_id,
        merchant_id=merchant_id,
        items=[
            MerchantCartItem(
                product_id=product["id"],
                product_title=product["title"],
                quantity=payload.quantity,
                unit_price=product["price"],
                total_price=subtotal
            )
        ],
        subtotal=subtotal,
        tax=tax,
        shipping_fee=shipping,
        discount=0.0,
        grand_total=grand_total,
        updated_at=datetime.now(timezone.utc).isoformat()
    )
    MERCHANT_CARTS[merchant_id][cart_id] = cart
    return cart

# -------------------------------------------------------------
# 4. PATCH /api/merchants/{merchant_id}/cart/{id}
# -------------------------------------------------------------
@merchant_sim_router.patch("/{merchant_id}/cart/{cart_id}", response_model=MerchantCart)
async def patch_merchant_cart(merchant_id: str = Path(...), cart_id: str = Path(...), payload: PatchCartPayload = Body(...)):
    """4. PATCH /cart/{id} — Update item quantities in merchant cart."""
    _validate_merchant_id(merchant_id)
    cart = MERCHANT_CARTS[merchant_id].get(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail=f"Cart '{cart_id}' not found at {merchant_id}")

    if cart.items:
        cart.items[0].quantity = payload.quantity
        cart.items[0].total_price = cart.items[0].unit_price * payload.quantity
        cart.subtotal = cart.items[0].total_price
        cart.tax = round(cart.subtotal * 0.18, 2)
        cart.grand_total = cart.subtotal + cart.tax + cart.shipping_fee - cart.discount
        cart.updated_at = datetime.now(timezone.utc).isoformat()

    return cart

# -------------------------------------------------------------
# 5. POST /api/merchants/{merchant_id}/checkout
# -------------------------------------------------------------
@merchant_sim_router.post("/{merchant_id}/checkout", response_model=MerchantQuote)
async def merchant_checkout(merchant_id: str = Path(...), payload: CheckoutPayload = Body(...)):
    """5. POST /checkout — Generates binding pricing quote with dynamic promo discounts."""
    _validate_merchant_id(merchant_id)
    cart = MERCHANT_CARTS[merchant_id].get(payload.cart_id)
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail=f"Cart '{payload.cart_id}' is empty or invalid at {merchant_id}")

    discount = 0.0
    if payload.promo_code and payload.promo_code in MERCHANT_CONFIGS[merchant_id]["supported_promos"]:
        discount_rate = MERCHANT_CONFIGS[merchant_id]["supported_promos"][payload.promo_code]
        discount = round(cart.subtotal * discount_rate, 2)

    grand_total = cart.subtotal + cart.tax + cart.shipping_fee - discount
    quote_id = f"q_{merchant_id}_{uuid.uuid4().hex[:6]}"
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()

    quote = MerchantQuote(
        quote_id=quote_id,
        merchant_id=merchant_id,
        cart_id=payload.cart_id,
        subtotal=cart.subtotal,
        tax_gst_18=cart.tax,
        shipping_fee=cart.shipping_fee,
        discount=discount,
        grand_total=grand_total,
        expires_at=expires_at
    )
    MERCHANT_QUOTES[merchant_id][quote_id] = quote
    return quote

# -------------------------------------------------------------
# 6. POST /api/merchants/{merchant_id}/payment
# -------------------------------------------------------------
@merchant_sim_router.post("/{merchant_id}/payment", response_model=MerchantOrder)
async def merchant_payment(merchant_id: str = Path(...), payload: PaymentPayload = Body(...)):
    """6. POST /payment — Settles tokenized payment and issues confirmed order."""
    _validate_merchant_id(merchant_id)
    quote = MERCHANT_QUOTES[merchant_id].get(payload.quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Quote '{payload.quote_id}' not found or expired at {merchant_id}")

    cart = MERCHANT_CARTS[merchant_id].get(quote.cart_id)
    items = cart.items if cart else []

    order_id = f"ORD_{merchant_id.upper().replace('-', '_')}_{uuid.uuid4().hex[:6].upper()}"
    now = datetime.now(timezone.utc)
    eta = (now + timedelta(days=MERCHANT_CONFIGS[merchant_id]["delivery_days"])).strftime("%A, %B %d, %Y")

    order = MerchantOrder(
        order_id=order_id,
        merchant_id=merchant_id,
        merchant_name=MERCHANT_CONFIGS[merchant_id]["name"],
        items=items,
        total_amount=quote.grand_total,
        payment_status="SETTLED",
        order_status="CONFIRMED",
        tracking_number=f"TRK-{merchant_id[:3].upper()}-{uuid.uuid4().hex[:6].upper()}",
        estimated_delivery=eta,
        created_at=now.isoformat(),
        shipping_address=payload.shipping_address or "Default Customer Address"
    )
    MERCHANT_ORDERS[merchant_id][order_id] = order
    return order

# -------------------------------------------------------------
# 7. GET /api/merchants/{merchant_id}/orders/{id}
# -------------------------------------------------------------
@merchant_sim_router.get("/{merchant_id}/orders/{order_id}", response_model=MerchantOrder)
async def get_merchant_order(merchant_id: str = Path(...), order_id: str = Path(...)):
    """7. GET /orders/{id} — Retrieve live order status & carrier tracking."""
    _validate_merchant_id(merchant_id)
    order = MERCHANT_ORDERS[merchant_id].get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found at {merchant_id}")
    return order

# -------------------------------------------------------------
# 8. POST /api/merchants/{merchant_id}/returns
# -------------------------------------------------------------
@merchant_sim_router.post("/{merchant_id}/returns/{order_id}", response_model=MerchantOrder)
async def return_merchant_order(merchant_id: str = Path(...), order_id: str = Path(...), payload: ReturnPayload = Body(...)):
    """8. POST /returns — Initiates autonomous return and refund workflow."""
    _validate_merchant_id(merchant_id)
    order = MERCHANT_ORDERS[merchant_id].get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found at {merchant_id}")

    order.order_status = "RETURN_REQUESTED"
    order.return_reason = payload.reason
    return order
