"""
Phase 2: Product & Search API Endpoints
Provides deterministic catalog search, filtering, product specs, inventory inspection, and cross-merchant price comparison.
"""
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db_session
from backend.domain.marketplace import (
    ProductSearchRequest, ProductSearchResponse, ProductDetail,
    CrossMerchantComparison, InventoryCheckResponse, ProductSortOption, AvailabilityState
)
from backend.services.catalog_service import CatalogService
from backend.services.inventory_service import InventoryService
from backend.core.errors import EntityNotFoundException

products_router = APIRouter(tags=["Products & Search"])


@products_router.get(
    "/products",
    response_model=ProductSearchResponse,
    summary="Search & Filter Products",
    description="Deterministic multi-attribute product search with brand, category, price, and rating filters."
)
def search_products(
    query: Optional[str] = Query(None, description="Search keyword matching title, brand, or model"),
    merchant_code: Optional[str] = Query(None, description="Filter by merchant: AMAZON | FLIPKART | CROMA"),
    category: Optional[str] = Query(None, description="Category filter (e.g. laptops, smartphones, headphones)"),
    brand: Optional[str] = Query(None, description="Brand filter (e.g. Apple, ASUS, Sony, Dell)"),
    min_price: Optional[Decimal] = Query(None, description="Minimum price filter in INR"),
    max_price: Optional[Decimal] = Query(None, description="Maximum price filter in INR"),
    min_rating: Optional[float] = Query(None, description="Minimum customer star rating (e.g. 4.0)"),
    in_stock_only: bool = Query(False, description="Filter out products with 0 stock"),
    sort_by: ProductSortOption = Query(ProductSortOption.RELEVANCE, description="Sort order"),
    page: int = Query(1, ge=1, description="Page index"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db_session)
) -> ProductSearchResponse:
    params = ProductSearchRequest(
        query=query,
        merchant_code=merchant_code,
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        in_stock_only=in_stock_only,
        sort_by=sort_by,
        page=page,
        page_size=page_size
    )
    return CatalogService.search_products(db, params)


@products_router.get(
    "/search",
    response_model=ProductSearchResponse,
    summary="Global Catalog Search Endpoint",
    description="Convenience search endpoint matching `/api/v1/search`."
)
def search_alias(
    q: Optional[str] = Query(None, description="Search query string"),
    merchant: Optional[str] = Query(None, description="Merchant code"),
    category: Optional[str] = Query(None, description="Category"),
    min_price: Optional[Decimal] = Query(None, description="Min price in INR"),
    max_price: Optional[Decimal] = Query(None, description="Max price in INR"),
    sort_by: ProductSortOption = Query(ProductSortOption.RELEVANCE, description="Sort by"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_session)
) -> ProductSearchResponse:
    params = ProductSearchRequest(
        query=q,
        merchant_code=merchant,
        category=category,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        page=page,
        page_size=page_size
    )
    return CatalogService.search_products(db, params)


@products_router.get(
    "/products/compare/{model_or_sku}",
    response_model=CrossMerchantComparison,
    summary="Cross-Merchant Product Comparison",
    description="Compares overlapping product listings across Amazon, Flipkart, and Croma for price, stock, and delivery speed."
)
def compare_cross_merchant(
    model_or_sku: str,
    db: Session = Depends(get_db_session)
) -> CrossMerchantComparison:
    comparison = CatalogService.compare_cross_merchant(db, model_or_sku)
    if not comparison:
        raise EntityNotFoundException("ProductComparison", model_or_sku, message=f"No matching products found across merchants for '{model_or_sku}'.")
    return comparison


@products_router.get(
    "/products/{product_id}",
    response_model=ProductDetail,
    summary="Get Product Details",
    description="Fetches comprehensive specifications, live inventory availability, and shipping options for a product."
)
def get_product(
    product_id: str,
    db: Session = Depends(get_db_session)
) -> ProductDetail:
    product = CatalogService.get_product_detail(db, product_id)
    if not product:
        raise EntityNotFoundException("Product", product_id)
    return product


@products_router.get(
    "/inventory/{product_id}",
    response_model=InventoryCheckResponse,
    summary="Check Live Inventory",
    description="Direct inventory inspection returning stock availability state and fulfillable quantity."
)
def check_inventory(
    product_id: str,
    quantity: int = Query(1, ge=1, description="Quantity requested to check"),
    db: Session = Depends(get_db_session)
) -> InventoryCheckResponse:
    prod = CatalogService.get_product_by_id(db, product_id)
    if not prod:
        raise EntityNotFoundException("Product", product_id)

    can_fulfill, avail_qty, state = InventoryService.check_availability(db, product_id, quantity)
    return InventoryCheckResponse(
        product_id=product_id,
        merchant_code=prod.merchant.merchant_code if prod.merchant else "MERCHANT",
        is_available=(avail_qty > 0),
        available_quantity=avail_qty,
        availability_state=AvailabilityState(state),
        can_fulfill_quantity=can_fulfill
    )
