"""
Phase 2: Product Catalog & Multi-Merchant Search Service
Provides deterministic catalog filtering, cross-merchant product comparison, and search.
"""
from decimal import Decimal
import math
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, desc, asc

from backend.database.models import ProductModel, MerchantModel, InventoryModel, ShippingOptionModel
from backend.domain.marketplace import (
    ProductSearchRequest, ProductSearchResponse, ProductSummary, ProductDetail,
    CrossMerchantComparison, CrossMerchantProductOffer, ProductSortOption, AvailabilityState
)
from backend.services.pricing_service import quantize_money


class CatalogService:
    """
    Deterministic product catalog and search service.
    """

    @staticmethod
    def get_product_by_id(db: Session, product_id: str) -> Optional[ProductModel]:
        """Fetches product by ID with merchant and inventory eagerly loaded."""
        return db.query(ProductModel).options(
            joinedload(ProductModel.merchant),
            joinedload(ProductModel.inventory)
        ).filter(
            ProductModel.id == product_id,
            ProductModel.is_active == True
        ).first()

    @staticmethod
    def get_product_detail(db: Session, product_id: str) -> Optional[ProductDetail]:
        """Constructs rich ProductDetail DTO with shipping options and computed metrics."""
        prod = CatalogService.get_product_by_id(db, product_id)
        if not prod:
            return None

        # Fetch active shipping options for this product's merchant
        shipping_options = db.query(ShippingOptionModel).filter(
            ShippingOptionModel.merchant_id == prod.merchant_id,
            ShippingOptionModel.is_active == True
        ).all()

        # Compute discount percentage if base_price > current_price
        disc_pct = 0.0
        if prod.base_price and prod.current_price and prod.base_price > prod.current_price:
            diff = prod.base_price - prod.current_price
            disc_pct = round(float((diff / prod.base_price) * Decimal("100.0")), 1)

        inv_state = AvailabilityState.IN_STOCK
        avail_qty = 0
        if prod.inventory:
            inv_state = AvailabilityState(prod.inventory.availability_state)
            avail_qty = prod.inventory.available_quantity

        return ProductDetail(
            id=prod.id,
            merchant_id=prod.merchant_id,
            merchant_code=prod.merchant.merchant_code if prod.merchant else None,
            merchant_name=prod.merchant.display_name if prod.merchant else None,
            sku=prod.sku,
            title=prod.title,
            brand=prod.brand,
            category=prod.category,
            model=prod.model,
            description=prod.description,
            base_price=quantize_money(prod.base_price),
            current_price=quantize_money(prod.current_price),
            currency=prod.currency,
            rating=prod.rating,
            review_count=prod.review_count,
            specs=prod.specs or {},
            image_url=prod.image_url,
            inventory_state=inv_state,
            available_quantity=avail_qty,
            discount_percentage=disc_pct,
            shipping_options=[opt.to_dict() for opt in shipping_options],
            is_active=prod.is_active,
            created_at=prod.created_at.isoformat() if prod.created_at else None,
            updated_at=prod.updated_at.isoformat() if prod.updated_at else None
        )

    @staticmethod
    def search_products(db: Session, params: ProductSearchRequest) -> ProductSearchResponse:
        """
        Executes deterministic multi-attribute product search across merchants.
        """
        query = db.query(ProductModel).options(
            joinedload(ProductModel.merchant),
            joinedload(ProductModel.inventory)
        ).join(MerchantModel).filter(
            ProductModel.is_active == True,
            MerchantModel.is_active == True
        )

        # 1. Filter by Merchant Code
        if params.merchant_code:
            query = query.filter(func.upper(MerchantModel.merchant_code) == params.merchant_code.strip().upper())

        # 2. Filter by Category
        if params.category:
            query = query.filter(func.lower(ProductModel.category) == params.category.strip().lower())

        # 3. Filter by Brand
        if params.brand:
            query = query.filter(func.lower(ProductModel.brand) == params.brand.strip().lower())

        # 4. Filter by Price Range
        if params.min_price is not None:
            query = query.filter(ProductModel.current_price >= params.min_price)
        if params.max_price is not None:
            query = query.filter(ProductModel.current_price <= params.max_price)

        # 5. Filter by Minimum Rating
        if params.min_rating is not None:
            query = query.filter(ProductModel.rating >= params.min_rating)

        # 6. Keyword Search (title, description, brand, model)
        if params.query:
            q_clean = f"%{params.query.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(ProductModel.title).like(q_clean),
                    func.lower(ProductModel.brand).like(q_clean),
                    func.lower(ProductModel.model).like(q_clean),
                    func.lower(ProductModel.description).like(q_clean),
                    func.lower(ProductModel.category).like(q_clean)
                )
            )

        # 7. Availability filter
        if params.in_stock_only:
            query = query.join(InventoryModel).filter(InventoryModel.available_quantity > 0)

        # Total count before pagination
        total_count = query.count()

        # 8. Sorting
        if params.sort_by == ProductSortOption.PRICE_LOW_TO_HIGH:
            query = query.order_by(ProductModel.current_price.asc())
        elif params.sort_by == ProductSortOption.PRICE_HIGH_TO_LOW:
            query = query.order_by(ProductModel.current_price.desc())
        elif params.sort_by == ProductSortOption.RATING:
            query = query.order_by(ProductModel.rating.desc(), ProductModel.review_count.desc())
        elif params.sort_by == ProductSortOption.POPULARITY:
            query = query.order_by(ProductModel.review_count.desc(), ProductModel.rating.desc())
        else:  # RELEVANCE (default)
            query = query.order_by(ProductModel.rating.desc(), ProductModel.current_price.asc())

        # 9. Pagination
        offset = (params.page - 1) * params.page_size
        products = query.offset(offset).limit(params.page_size).all()

        items = []
        for p in products:
            inv_state = AvailabilityState.IN_STOCK
            avail_qty = 0
            if p.inventory:
                inv_state = AvailabilityState(p.inventory.availability_state)
                avail_qty = p.inventory.available_quantity

            items.append(ProductSummary(
                id=p.id,
                merchant_id=p.merchant_id,
                merchant_code=p.merchant.merchant_code if p.merchant else None,
                merchant_name=p.merchant.display_name if p.merchant else None,
                sku=p.sku,
                title=p.title,
                brand=p.brand,
                category=p.category,
                model=p.model,
                description=p.description,
                specs=p.specs or {},
                base_price=quantize_money(p.base_price),
                current_price=quantize_money(p.current_price),
                currency=p.currency,
                rating=p.rating,
                review_count=p.review_count,
                image_url=p.image_url,
                inventory_state=inv_state,
                available_quantity=avail_qty,
                is_active=p.is_active
            ))

        total_pages = max(1, math.ceil(total_count / params.page_size))
        return ProductSearchResponse(
            items=items,
            total_count=total_count,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            query_echo=params.model_dump(exclude_none=True)
        )

    @staticmethod
    def compare_cross_merchant(db: Session, model_or_sku: str) -> Optional[CrossMerchantComparison]:
        """
        Finds overlapping product listings across Amazon, Flipkart, and Croma for a model.
        Returns unified comparison of prices, stock, delivery speed, and best offer.
        """
        clean_model = model_or_sku.strip().lower()
        products = db.query(ProductModel).options(
            joinedload(ProductModel.merchant),
            joinedload(ProductModel.inventory)
        ).join(MerchantModel).filter(
            or_(
                func.lower(ProductModel.model) == clean_model,
                func.lower(ProductModel.sku).like(f"%{clean_model}%"),
                func.lower(ProductModel.title).like(f"%{clean_model}%")
            ),
            ProductModel.is_active == True,
            MerchantModel.is_active == True
        ).all()

        if not products:
            return None

        offers: List[CrossMerchantProductOffer] = []
        for p in products:
            # Calculate discount
            disc_pct = 0.0
            if p.base_price and p.current_price and p.base_price > p.current_price:
                diff = p.base_price - p.current_price
                disc_pct = round(float((diff / p.base_price) * Decimal("100.0")), 1)

            # Get cheapest shipping option
            cheapest_ship = db.query(ShippingOptionModel).filter(
                ShippingOptionModel.merchant_id == p.merchant_id,
                ShippingOptionModel.is_active == True
            ).order_by(ShippingOptionModel.cost.asc()).first()

            ship_cost = quantize_money(cheapest_ship.cost if cheapest_ship else Decimal("0.00"))
            deliv_days = cheapest_ship.estimated_days if cheapest_ship else 3

            inv_state = AvailabilityState.IN_STOCK
            avail_qty = 0
            if p.inventory:
                inv_state = AvailabilityState(p.inventory.availability_state)
                avail_qty = p.inventory.available_quantity

            offers.append(CrossMerchantProductOffer(
                merchant_code=p.merchant.merchant_code,
                merchant_name=p.merchant.display_name,
                product_id=p.id,
                sku=p.sku,
                current_price=quantize_money(p.current_price),
                base_price=quantize_money(p.base_price),
                discount_percentage=disc_pct,
                inventory_state=inv_state,
                available_quantity=avail_qty,
                delivery_days=deliv_days,
                shipping_cost=ship_cost,
                rating=p.rating
            ))

        # Sort offers by lowest price
        offers_by_price = sorted(offers, key=lambda o: (o.current_price + o.shipping_cost))
        offers_by_speed = sorted(offers, key=lambda o: o.delivery_days)

        best_price = offers_by_price[0] if offers_by_price else None
        fastest_deliv = offers_by_speed[0] if offers_by_speed else None

        ref_product = products[0]
        return CrossMerchantComparison(
            model_or_title=ref_product.model or ref_product.title,
            category=ref_product.category,
            brand=ref_product.brand,
            best_price_offer=best_price,
            fastest_delivery_offer=fastest_deliv,
            all_offers=offers
        )
