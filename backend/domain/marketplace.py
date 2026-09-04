"""
Phase 2: Merchant Marketplace Simulator Domain Schemas & DTOs (Pydantic v2)
Defines strictly typed request, response, and transfer models with Decimal financial precision.
"""
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# =====================================================================
# Enums
# =====================================================================

class MerchantCode(str, Enum):
    AMAZON = "AMAZON"
    FLIPKART = "FLIPKART"
    CROMA = "CROMA"


class AvailabilityState(str, Enum):
    IN_STOCK = "IN_STOCK"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class DiscountType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FLAT = "FLAT"


class ShippingMethodType(str, Enum):
    STANDARD = "STANDARD"
    EXPRESS = "EXPRESS"
    SAME_DAY = "SAME_DAY"
    STORE_PICKUP = "STORE_PICKUP"


class CartStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MERGED = "MERGED"
    CHECKED_OUT = "CHECKED_OUT"
    ABANDONED = "ABANDONED"


class CheckoutSessionStatus(str, Enum):
    QUOTE_CREATED = "QUOTE_CREATED"
    QUOTE_VALID = "QUOTE_VALID"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
    AUTHORIZED = "AUTHORIZED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    ORDER_PENDING = "ORDER_PENDING"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    INVALID = "INVALID"
    PENDING = "PENDING"  # Backward-compatible alias for QUOTE_CREATED


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class ProductSortOption(str, Enum):
    RELEVANCE = "relevance"
    PRICE_LOW_TO_HIGH = "price_low_to_high"
    PRICE_HIGH_TO_LOW = "price_high_to_low"
    RATING = "rating"
    POPULARITY = "popularity"


# =====================================================================
# Merchant Schemas
# =====================================================================

class MerchantSummary(BaseModel):
    id: str
    merchant_code: str
    display_name: str
    description: Optional[str] = None
    is_active: bool = True
    rating: float = 4.8
    logo_url: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MerchantDetail(MerchantSummary):
    shipping_options_count: int = 0
    active_products_count: int = 0
    active_promotions_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# =====================================================================
# Product & Catalog Schemas
# =====================================================================

class ProductSummary(BaseModel):
    id: str
    merchant_id: str
    merchant_code: Optional[str] = None
    merchant_name: Optional[str] = None
    sku: str
    title: str
    brand: str
    category: str
    model: Optional[str] = None
    description: Optional[str] = None
    specs: Dict[str, Any] = Field(default_factory=dict)
    base_price: Decimal = Field(..., decimal_places=2)
    current_price: Decimal = Field(..., decimal_places=2)
    currency: str = "INR"
    rating: float = 4.5
    review_count: int = 0
    image_url: Optional[str] = None
    inventory_state: AvailabilityState = AvailabilityState.IN_STOCK
    available_quantity: int = 0
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class ProductDetail(ProductSummary):
    shipping_options: List[Dict[str, Any]] = Field(default_factory=list)
    discount_percentage: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProductSearchRequest(BaseModel):
    query: Optional[str] = None
    merchant_code: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_rating: Optional[float] = None
    in_stock_only: bool = False
    sort_by: ProductSortOption = ProductSortOption.RELEVANCE
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ProductSearchResponse(BaseModel):
    items: List[ProductSummary]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    query_echo: Dict[str, Any] = Field(default_factory=dict)


class CrossMerchantProductOffer(BaseModel):
    merchant_code: str
    merchant_name: str
    product_id: str
    sku: str
    current_price: Decimal
    base_price: Decimal
    discount_percentage: float
    inventory_state: AvailabilityState
    available_quantity: int
    delivery_days: int
    shipping_cost: Decimal
    rating: float


class CrossMerchantComparison(BaseModel):
    model_or_title: str
    category: str
    brand: str
    best_price_offer: Optional[CrossMerchantProductOffer] = None
    fastest_delivery_offer: Optional[CrossMerchantProductOffer] = None
    all_offers: List[CrossMerchantProductOffer] = Field(default_factory=list)


# =====================================================================
# Inventory Schemas
# =====================================================================

class InventoryDetail(BaseModel):
    id: str
    product_id: str
    merchant_id: str
    available_quantity: int
    reserved_quantity: int
    sold_quantity: int
    availability_state: AvailabilityState
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InventoryCheckResponse(BaseModel):
    product_id: str
    merchant_code: str
    is_available: bool
    available_quantity: int
    availability_state: AvailabilityState
    can_fulfill_quantity: bool = True


# =====================================================================
# Pricing, Discounts & Shipping Schemas
# =====================================================================

class DiscountDetail(BaseModel):
    id: str
    merchant_id: str
    code: str
    description: Optional[str] = None
    discount_type: DiscountType
    discount_value: Decimal
    min_order_value: Decimal = Decimal("0.00")
    max_discount: Optional[Decimal] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class ShippingOptionDetail(BaseModel):
    id: str
    merchant_id: str
    code: str
    name: str
    cost: Decimal
    estimated_days: int
    delivery_type: str
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# Cart Schemas
# =====================================================================

class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1, le=100)
    expected_price: Optional[Decimal] = None


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=0, le=100)


class CartItemDetail(BaseModel):
    id: str
    cart_id: str
    product_id: str
    product_title: Optional[str] = None
    sku: Optional[str] = None
    image_url: Optional[str] = None
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    is_available: bool = True
    available_quantity: Optional[int] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CartCreateRequest(BaseModel):
    merchant_code: str
    session_id: Optional[str] = None


class CartDetail(BaseModel):
    id: str
    merchant_id: str
    merchant_code: Optional[str] = None
    merchant_name: Optional[str] = None
    session_id: Optional[str] = None
    items: List[CartItemDetail] = Field(default_factory=list)
    items_count: int = 0
    subtotal: Decimal = Decimal("0.00")
    discount_total: Decimal = Decimal("0.00")
    shipping_total: Decimal = Decimal("0.00")
    tax_total: Decimal = Decimal("0.00")
    grand_total: Decimal = Decimal("0.00")
    currency: str = "INR"
    status: CartStatus = CartStatus.ACTIVE
    is_stale: bool = False
    warnings: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecommendationSelectionRequest(BaseModel):
    """
    Explicit user selection contract to transfer a recommended product into an authoritative merchant cart.
    Client-provided monetary or inventory fields are strictly omitted.
    """
    product_id: str = Field(..., description="Unique product ID or canonical identifier")
    merchant_code: str = Field(..., description="Merchant identifier (e.g. AMAZON, FLIPKART, CROMA)")
    quantity: int = Field(default=1, ge=1, le=100, description="Requested units to add")
    session_id: Optional[str] = Field(default=None, description="Active shopping session ID")
    cart_id: Optional[str] = Field(default=None, description="Optional existing merchant cart ID to reuse")
    expected_price: Optional[Decimal] = Field(default=None, description="Informational price displayed at recommendation time for change detection")


class RecommendationSelectionResponse(BaseModel):
    """
    Response returned upon server-side validation and cart mutation.
    """
    success: bool = Field(default=True, description="True if product was validated and added to cart")
    cart: CartDetail = Field(..., description="Server-recalculated authoritative cart state")
    price_changed: bool = Field(default=False, description="True if live catalog price differs from recommendation expected price")
    original_expected_price: Optional[Decimal] = Field(default=None, description="Recommendation price before live validation")
    current_authoritative_price: Decimal = Field(..., description="Live database catalog price applied to cart")
    message: str = Field(default="Product successfully added to cart", description="User-facing summary message")


# =====================================================================
# Checkout Schemas
# =====================================================================

class CheckoutPrepareRequest(BaseModel):
    cart_id: str
    shipping_option_id: Optional[str] = None
    promo_code: Optional[str] = None
    shipping_address: Optional[str] = None
    session_id: Optional[str] = None


class CheckoutItemSummary(BaseModel):
    product_id: str
    product_title: str
    sku: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal


class CheckoutSummaryResponse(BaseModel):
    checkout_session_id: str
    quote_id: Optional[str] = None
    cart_id: str
    merchant_code: str
    merchant_name: str
    subtotal: Decimal
    discount_total: Decimal
    shipping_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
    currency: str = "INR"
    items: List[CheckoutItemSummary] = Field(default_factory=list)
    shipping_option: Optional[ShippingOptionDetail] = None
    applied_promo: Optional[str] = None
    status: CheckoutSessionStatus = CheckoutSessionStatus.PENDING
    price_changed: bool = False
    is_stale: bool = False
    warnings: List[str] = Field(default_factory=list)
    state_history: List[Dict[str, Any]] = Field(default_factory=list)
    version: int = 1
    expires_at: str
    created_at: str


class CheckoutTransitionAction(str, Enum):
    VALIDATE_QUOTE = "validate_quote"
    REQUEST_AUTHORIZATION = "request_authorization"
    AUTHORIZE = "authorize"
    INITIATE_PAYMENT = "initiate_payment"
    CONFIRM_PAYMENT = "confirm_payment"
    SUBMIT_ORDER = "submit_order"
    COMPLETE = "complete"
    CANCEL = "cancel"
    FAIL = "fail"
    INVALIDATE = "invalidate"


class CheckoutTransitionRequest(BaseModel):
    action: CheckoutTransitionAction = Field(..., description="Semantic action to execute on checkout session")
    reason: Optional[str] = Field(default=None, description="Optional explanation or context for transition")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context metadata")
    quote_id: Optional[str] = Field(default=None, description="Optional quote ID to verify binding")
    cart_id: Optional[str] = Field(default=None, description="Optional cart ID to verify binding")
    merchant_code: Optional[str] = Field(default=None, description="Optional merchant code to verify binding")

    model_config = ConfigDict(extra="forbid")


class StateTransitionAuditLog(BaseModel):
    previous_state: str
    target_state: str
    action: str
    timestamp: str
    reason: Optional[str] = None
    success: bool = True


class CheckoutTransitionResponse(BaseModel):
    success: bool = True
    message: str
    checkout_session_id: str
    previous_state: str
    current_state: CheckoutSessionStatus
    action: CheckoutTransitionAction
    checkout: CheckoutSummaryResponse
    audit_log: Optional[StateTransitionAuditLog] = None


# =====================================================================
# Order Schemas
# =====================================================================

class OrderCreateRequest(BaseModel):
    checkout_session_id: str
    shipping_address: str = Field(..., min_length=10)
    payment_method: str = Field(default="UPI_SIMULATED")


class OrderItemDetail(BaseModel):
    id: str
    product_id: Optional[str] = None
    product_title: str
    sku: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderDetail(BaseModel):
    id: str
    order_number: str
    merchant_id: str
    merchant_code: Optional[str] = None
    merchant_name: Optional[str] = None
    session_id: Optional[str] = None
    items: List[OrderItemDetail] = Field(default_factory=list)
    subtotal: Decimal
    discount_total: Decimal
    shipping_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
    currency: str = "INR"
    shipping_address: str
    shipping_method: str
    payment_method: str
    status: OrderStatus
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderTrackingResponse(BaseModel):
    order_id: str
    order_number: str
    merchant_code: str
    status: OrderStatus
    tracking_number: Optional[str] = None
    carrier: str = "AgentCart Logistics Express"
    estimated_delivery: Optional[str] = None
    status_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    shipping_address: str
