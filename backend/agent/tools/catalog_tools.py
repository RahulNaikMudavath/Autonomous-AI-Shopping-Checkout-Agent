"""
Phase 3: Autonomous AI Shopping Agent Tools
Sandboxed read-only tools for catalog search, product detail retrieval, cross-merchant price comparison, and inventory verification.
Guaranteed safe: No tool in this module can mutate shopping carts, modify prices, or authorize payments.
"""
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.domain.marketplace import (
    ProductSearchRequest, ProductSearchResponse, ProductDetail,
    CrossMerchantComparison, ProductSortOption
)
from backend.services.catalog_service import CatalogService
from backend.services.inventory_service import InventoryService
from backend.trust_safety.untrusted_content_sanitizer import UntrustedContentSanitizer

logger = logging.getLogger("agentcart.agent.tools")


class CatalogTools:
    """
    Sandboxed read-only tool suite for autonomous product discovery and comparison.
    """

    @staticmethod
    def search_multi_merchant_catalog(
        db: Session,
        category: Optional[str] = None,
        query: Optional[str] = None,
        merchant_code: Optional[str] = None,
        brand: Optional[str] = None,
        max_price: Optional[Decimal] = None,
        min_price: Optional[Decimal] = None,
        min_rating: Optional[float] = None,
        in_stock_only: bool = True,
        sort_by: ProductSortOption = ProductSortOption.RELEVANCE,
        page: int = 1,
        page_size: int = 50
    ) -> ProductSearchResponse:
        """
        Federated search tool querying active merchant catalogs (Amazon, Flipkart, Croma).
        """
        request = ProductSearchRequest(
            category=category,
            query=query,
            merchant_code=merchant_code,
            brand=brand,
            max_price=max_price,
            min_price=min_price,
            min_rating=min_rating,
            in_stock_only=in_stock_only,
            sort_by=sort_by,
            page=page,
            page_size=page_size
        )
        response = CatalogService.search_products(db, request)
        
        # Sanitize merchant title strings before returning to agent
        for item in response.items:
            sanitized = UntrustedContentSanitizer.sanitize_merchant_content(
                raw_text=item.title,
                merchant_name=item.merchant_name or "Merchant",
                source_field="title"
            )
            item.title = sanitized.sanitized_clean_content

        return response

    @staticmethod
    def get_product_details(db: Session, product_id: str) -> Optional[ProductDetail]:
        """
        Retrieves rich product specifications, images, and merchant shipping tiers.
        """
        detail = CatalogService.get_product_detail(db, product_id)
        if detail:
            # Sanitize description & title
            if detail.description:
                san_desc = UntrustedContentSanitizer.sanitize_merchant_content(
                    raw_text=detail.description,
                    merchant_name=detail.merchant_name or "Merchant",
                    source_field="description"
                )
                detail.description = san_desc.sanitized_clean_content
        return detail

    @staticmethod
    def compare_cross_merchant_model(db: Session, model_number: str) -> Optional[CrossMerchantComparison]:
        """
        Retrieves cross-merchant price comparison matrix across Amazon, Flipkart, and Croma.
        """
        return CatalogService.compare_models_across_merchants(db, model_number)

    @staticmethod
    def check_live_inventory(db: Session, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """
        Performs authoritative real-time inventory and availability check.
        """
        can_fulfill, avail_qty, state = InventoryService.check_availability(db, product_id, quantity)
        return {
            "product_id": product_id,
            "can_fulfill": can_fulfill,
            "available_quantity": avail_qty,
            "availability_state": state.value if hasattr(state, "value") else str(state)
        }
