"""
Phase 2: Merchant Adapter Layer
Implements specialized, pluggable adapters for simulated merchants (Amazon, Flipkart, Croma).
Provides uniform interface for the Commerce Gateway while preserving merchant-specific differentiation.
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.database.models import MerchantModel, ProductModel, CartModel, OrderModel, ShippingOptionModel
from backend.domain.marketplace import (
    ProductSearchRequest, ProductSearchResponse, ProductDetail,
    CartDetail, CheckoutPrepareRequest, CheckoutSummaryResponse,
    OrderCreateRequest, OrderDetail, OrderTrackingResponse
)
from backend.services.catalog_service import CatalogService
from backend.services.inventory_service import InventoryService
from backend.services.shipping_service import ShippingService
from backend.services.cart_service import CartService
from backend.services.checkout_service import CheckoutService
from backend.services.order_service import OrderService
from backend.core.errors import EntityNotFoundException


class BaseMerchantAdapter(ABC):
    """
    Abstract contract for all simulated merchant integrations.
    """
    merchant_code: str
    display_name: str
    specialty: str

    def get_merchant_record(self, db: Session) -> Optional[MerchantModel]:
        return db.query(MerchantModel).filter(
            MerchantModel.merchant_code == self.merchant_code,
            MerchantModel.is_active == True
        ).first()

    def search_products(self, db: Session, params: ProductSearchRequest) -> ProductSearchResponse:
        params.merchant_code = self.merchant_code
        return CatalogService.search_products(db, params)

    def get_product(self, db: Session, product_id: str) -> Optional[ProductDetail]:
        return CatalogService.get_product_detail(db, product_id)

    def check_inventory(self, db: Session, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        can_fulfill, avail_qty, state = InventoryService.check_availability(db, product_id, quantity)
        return {
            "merchant_code": self.merchant_code,
            "product_id": product_id,
            "can_fulfill": can_fulfill,
            "available_quantity": avail_qty,
            "availability_state": state
        }

    def get_shipping_options(self, db: Session) -> List[Dict[str, Any]]:
        merchant = self.get_merchant_record(db)
        if not merchant:
            return []
        options = ShippingService.get_shipping_options(db, merchant.id)
        return [opt.to_dict() for opt in options]

    def create_cart(self, db: Session, session_id: Optional[str] = None) -> CartDetail:
        merchant = self.get_merchant_record(db)
        if not merchant:
            raise EntityNotFoundException("Merchant", self.merchant_code)
        cart = CartService.create_cart(db, merchant.id, session_id)
        return CartService.to_dto(cart)

    def add_to_cart(self, db: Session, cart_id: str, product_id: str, quantity: int = 1) -> CartDetail:
        cart = CartService.add_item_to_cart(db, cart_id, product_id, quantity)
        return CartService.to_dto(cart)

    def update_cart_item(self, db: Session, cart_id: str, item_id: str, quantity: int) -> CartDetail:
        cart = CartService.update_cart_item(db, cart_id, item_id, quantity)
        return CartService.to_dto(cart)

    def remove_from_cart(self, db: Session, cart_id: str, item_id: str) -> CartDetail:
        cart = CartService.remove_cart_item(db, cart_id, item_id)
        return CartService.to_dto(cart)

    def prepare_checkout(
        self,
        db: Session,
        cart_id: str,
        shipping_option_id: Optional[str] = None,
        promo_code: Optional[str] = None
    ) -> CheckoutSummaryResponse:
        req = CheckoutPrepareRequest(
            cart_id=cart_id,
            shipping_option_id=shipping_option_id,
            promo_code=promo_code
        )
        return CheckoutService.prepare_checkout(db, req)

    def create_order(
        self,
        db: Session,
        checkout_session_id: str,
        shipping_address: str,
        payment_method: str = "UPI_SIMULATED"
    ) -> OrderDetail:
        req = OrderCreateRequest(
            checkout_session_id=checkout_session_id,
            shipping_address=shipping_address,
            payment_method=payment_method
        )
        order = OrderService.create_order(db, req)
        return OrderService.to_dto(order)

    def get_order(self, db: Session, order_id_or_number: str) -> Optional[OrderDetail]:
        order = OrderService.get_order_by_id(db, order_id_or_number)
        if not order:
            return None
        return OrderService.to_dto(order)

    def track_order(self, db: Session, order_id_or_number: str) -> OrderTrackingResponse:
        return OrderService.track_order(db, order_id_or_number)


# =====================================================================
# Merchant Adapter Implementations
# =====================================================================

class AmazonMerchantAdapter(BaseMerchantAdapter):
    """
    Amazon Simulator Adapter:
    - Broad general catalog across all computing and lifestyle categories
    - Amazon Prime 1-2 day express shipping network
    - Large inventory depth
    """
    merchant_code = "AMAZON"
    display_name = "Amazon India"
    specialty = "Broad catalog, high stock availability & Prime Express delivery"


class FlipkartMerchantAdapter(BaseMerchantAdapter):
    """
    Flipkart Simulator Adapter:
    - Highly competitive mobile and tech pricing
    - Flipkart SuperCoins and seasonal developer promotions
    - Fast standard logistics
    """
    merchant_code = "FLIPKART"
    display_name = "Flipkart"
    specialty = "Competitive consumer electronics, smartphones & mega promotional discounts"


class CromaMerchantAdapter(BaseMerchantAdapter):
    """
    Croma Simulator Adapter:
    - Electronics specialist (monitors, laptops, premium audio)
    - Express store pickup & same-day city delivery options
    - Extended warranty coverage
    """
    merchant_code = "CROMA"
    display_name = "Croma Electronics"
    specialty = "Specialist computing, studio displays, high-end audio & store pickup"


# =====================================================================
# Adapter Registry Factory
# =====================================================================

_ADAPTER_REGISTRY: Dict[str, BaseMerchantAdapter] = {
    "AMAZON": AmazonMerchantAdapter(),
    "FLIPKART": FlipkartMerchantAdapter(),
    "CROMA": CromaMerchantAdapter(),
    # Backward compatibility aliases for Phase 1 tests
    "MERCHANT-A": AmazonMerchantAdapter(),
    "MERCHANT-B": FlipkartMerchantAdapter(),
    "MERCHANT-C": CromaMerchantAdapter(),
    "MERCHANT-D": AmazonMerchantAdapter(),
    "TECHHUB_IN": AmazonMerchantAdapter(),
    "ELECTROBAZAAR_IN": FlipkartMerchantAdapter(),
    "OMNISTORE_IN": CromaMerchantAdapter(),
    "PROHARDWARE_IN": AmazonMerchantAdapter(),
}


def get_merchant_adapter(merchant_code_or_id: str) -> BaseMerchantAdapter:
    """
    Resolves and returns the specialized adapter for the requested merchant code.
    Raises EntityNotFoundException if the merchant is unsupported.
    """
    clean_code = merchant_code_or_id.strip().upper()
    adapter = _ADAPTER_REGISTRY.get(clean_code)
    if not adapter:
        raise EntityNotFoundException("MerchantAdapter", merchant_code_or_id)
    return adapter


def list_merchant_adapters() -> List[BaseMerchantAdapter]:
    """Returns unique primary merchant adapters."""
    return [
        _ADAPTER_REGISTRY["AMAZON"],
        _ADAPTER_REGISTRY["FLIPKART"],
        _ADAPTER_REGISTRY["CROMA"]
    ]
