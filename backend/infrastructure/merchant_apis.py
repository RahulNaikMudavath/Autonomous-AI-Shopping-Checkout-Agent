"""
Layer 4: Commerce Infrastructure - Dedicated Merchant Service REST APIs
Provides 4 independent, realistic merchant REST endpoints:
- Merchant A (TechHub API)
- Merchant B (ElectroBazaar API)
- Merchant C (OmniStore API)
- Merchant D (ProHardware Direct API)
Simulates real enterprise commerce backends with inventory checking, dynamic quotes, and SLA metrics.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.infrastructure.merchants import PRODUCT_CATALOG, MERCHANTS

merchant_apis_router = APIRouter(prefix="/api/merchants", tags=["Merchant Commerce APIs"])

# -------------------------------------------------------------
# Merchant A — TechHub India API
# -------------------------------------------------------------
@merchant_apis_router.get("/a/catalog")
async def merchant_a_catalog(category: Optional[str] = None):
    """Merchant A (TechHub India) — High-Performance & AI Workstations."""
    products = [p for p in PRODUCT_CATALOG if p.merchant_id == "techhub_in"]
    if category:
        products = [p for p in products if p.category.lower() == category.lower()]
    return {
        "merchant": "Merchant A (TechHub India)",
        "api_version": "v2.4-enterprise",
        "currency": "INR",
        "express_logistics_active": True,
        "items": [
            {
                "sku": p.id,
                "title": p.title,
                "brand": p.brand,
                "price": p.price_inr,
                "mrp": p.original_price_inr,
                "specs": p.specs.model_dump(),
                "stock_status": "IN_STOCK" if p.in_stock else "OUT_OF_STOCK",
                "units_in_warehouse": p.stock_quantity,
                "delivery_sla_days": p.delivery_days
            }
            for p in products
        ]
    }

@merchant_apis_router.get("/a/inventory/{sku}")
async def merchant_a_inventory(sku: str):
    product = next((p for p in PRODUCT_CATALOG if p.id == sku and p.merchant_id == "techhub_in"), None)
    if not product:
        raise HTTPException(status_code=404, detail=f"SKU {sku} not found at Merchant A")
    return {
        "sku": sku,
        "in_stock": product.in_stock,
        "quantity": product.stock_quantity,
        "warehouse_location": "Bangalore Hub 1",
        "next_day_dispatch_eligible": True
    }

# -------------------------------------------------------------
# Merchant B — ElectroBazaar API
# -------------------------------------------------------------
@merchant_apis_router.get("/b/search")
async def merchant_b_search(q: Optional[str] = None, max_price: Optional[float] = None):
    """Merchant B (ElectroBazaar) — Electronics & Consumer Deals."""
    products = [p for p in PRODUCT_CATALOG if p.merchant_id == "electrobazaar_in"]
    if max_price:
        products = [p for p in products if p.price_inr <= max_price]
    return {
        "vendor": "Merchant B (ElectroBazaar Online)",
        "feed_timestamp": "2026-09-03T18:00:00Z",
        "results_count": len(products),
        "listings": [
            {
                "product_id": p.id,
                "name": p.title,
                "selling_price_inr": p.price_inr,
                "list_price_inr": p.original_price_inr,
                "discount_percentage": round(((p.original_price_inr - p.price_inr) / p.original_price_inr) * 100),
                "hardware_profile": p.specs.model_dump(),
                "available_stock": p.stock_quantity,
                "ratings_summary": {"stars": p.rating, "reviews": p.review_count}
            }
            for p in products
        ]
    }

# -------------------------------------------------------------
# Merchant C — OmniStore API
# -------------------------------------------------------------
@merchant_apis_router.get("/c/products")
async def merchant_c_products():
    """Merchant C (OmniStore Online) — Mass Marketplace & Extended Warranty."""
    products = [p for p in PRODUCT_CATALOG if p.merchant_id == "omnistore_in"]
    return {
        "provider": "Merchant C (OmniStore Global)",
        "catalog_type": "mass_retail",
        "active_offers": ["EXTRA_1YR_WARRANTY", "FREE_ACCIDENTAL_COVER"],
        "items": [
            {
                "item_code": p.id,
                "headline": p.title,
                "current_price": p.price_inr,
                "specifications": p.specs.model_dump(),
                "inventory_count": p.stock_quantity,
                "shipping_charges": p.shipping_fee_inr
            }
            for p in products
        ]
    }

# -------------------------------------------------------------
# Merchant D — ProHardware Direct API
# -------------------------------------------------------------
@merchant_apis_router.get("/d/enterprise-catalog")
async def merchant_d_catalog():
    """Merchant D (ProHardware Direct) — Enterprise OEM & High-Memory Dev Workstations."""
    products = [p for p in PRODUCT_CATALOG if p.merchant_id == "prohardware_in"]
    return {
        "distributor": "Merchant D (ProHardware Direct OEM)",
        "tier": "enterprise_tier_1",
        "b2b_invoicing": True,
        "workstations": [
            {
                "oem_id": p.id,
                "model_name": p.title,
                "enterprise_price_inr": p.price_inr,
                "specs": p.specs.model_dump(),
                "stock_available": p.stock_quantity,
                "lead_time_days": p.delivery_days,
                "warranty_terms": f"{p.warranty_years} Years ProSupport Plus"
            }
            for p in products
        ]
    }

@merchant_apis_router.get("/directory")
async def get_all_merchant_metadata():
    """Directory listing all 4 active merchant APIs and SLA health."""
    return {
        "total_merchants": 4,
        "merchants": [
            {
                "id": "merchant_a",
                "name": "Merchant A (TechHub India)",
                "api_endpoint": "/api/merchants/a/catalog",
                "status": "HEALTHY",
                "specialty": "AI/ML Workstations & High-TGP GPUs",
                "reputation": 4.9
            },
            {
                "id": "merchant_b",
                "name": "Merchant B (ElectroBazaar)",
                "api_endpoint": "/api/merchants/b/search",
                "status": "HEALTHY",
                "specialty": "Consumer Electronics & Value Pricing",
                "reputation": 4.7
            },
            {
                "id": "merchant_c",
                "name": "Merchant C (OmniStore Online)",
                "api_endpoint": "/api/merchants/c/products",
                "status": "HEALTHY",
                "specialty": "Mass Catalog & Extended Warranties",
                "reputation": 4.6
            },
            {
                "id": "merchant_d",
                "name": "Merchant D (ProHardware Direct)",
                "api_endpoint": "/api/merchants/d/enterprise-catalog",
                "status": "HEALTHY",
                "specialty": "Enterprise OEM & High Memory Rigs",
                "reputation": 4.8
            }
        ]
    }
