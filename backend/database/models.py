"""
AgentCart Database Domain Models (PostgreSQL / SQLAlchemy 2.0)
Defines foundational domain entities for Phase 1:
- User: Core user identity and account state
- UserPreference: Personalization, shipping constraints, budget/brand affinity
- ShoppingSession: Top-level conversation & shopping lifecycle container
- ShoppingTask: Structured discrete intent, requirements, and execution plan
- AgentRun: Execution telemetry, latency, token consumption, cost, and traces
- AuditEvent: Cryptographically chained tamper-evident compliance ledger
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text, Index, Numeric
)
from sqlalchemy.orm import declarative_base, relationship
from decimal import Decimal

Base = declarative_base()


def generate_uuid() -> str:
    """Generates a UUID4 string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Returns current UTC timestamp."""
    return datetime.now(timezone.utc)


class User(Base):
    """Represents an authenticated user in the AgentCart system."""
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("ShoppingSession", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class UserPreference(Base):
    """Represents personalized shopping constraints and affinities for a user."""
    __tablename__ = "user_preferences"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    brand_affinity = Column(JSON, default=list)  # e.g. ["Apple", "Sony", "Dell"]
    price_sensitivity = Column(String(32), default="balanced")  # "low", "balanced", "value", "premium"
    default_shipping_address = Column(Text, nullable=True)
    default_currency = Column(String(10), default="INR")
    max_auto_approval_budget = Column(Float, default=5000.0)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="preferences")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "brand_affinity": self.brand_affinity or [],
            "price_sensitivity": self.price_sensitivity,
            "default_shipping_address": self.default_shipping_address,
            "default_currency": self.default_currency,
            "max_auto_approval_budget": self.max_auto_approval_budget,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<UserPreference id={self.id} user_id={self.user_id}>"


class ShoppingSession(Base):
    """Represents a high-level shopping session holding one or more tasks and agent runs."""
    __tablename__ = "shopping_sessions"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Shopping Session", nullable=False)
    status = Column(String(32), default="ACTIVE", index=True, nullable=False)  # "ACTIVE", "COMPLETED", "ABORTED"
    session_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")
    tasks = relationship("ShoppingTask", back_populates="session", cascade="all, delete-orphan", order_by="ShoppingTask.created_at")
    agent_runs = relationship("AgentRun", back_populates="session", cascade="all, delete-orphan", order_by="AgentRun.created_at")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "status": self.status,
            "metadata": self.session_metadata or {},
            "tasks_count": len(self.tasks) if self.tasks else 0,
            "agent_runs_count": len(self.agent_runs) if self.agent_runs else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<ShoppingSession id={self.id} status={self.status}>"


class ShoppingTask(Base):
    """Represents a discrete shopping goal or parsed user query within a session."""
    __tablename__ = "shopping_tasks"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(64), ForeignKey("shopping_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_prompt = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING", index=True, nullable=False)  # "PENDING", "PLANNING", "DISCOVERING", "COMPLETED", "FAILED"
    extracted_constraints = Column(JSON, default=dict)
    execution_plan = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    session = relationship("ShoppingSession", back_populates="tasks")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "raw_prompt": self.raw_prompt,
            "status": self.status,
            "extracted_constraints": self.extracted_constraints or {},
            "execution_plan": self.execution_plan or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<ShoppingTask id={self.id} session_id={self.session_id} status={self.status}>"


class AgentRun(Base):
    """Tracks autonomous multi-agent execution telemetry, latency, token usage, and trace steps."""
    __tablename__ = "agent_runs"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(64), ForeignKey("shopping_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    supervisor_agent = Column(String(64), default="LangGraphSupervisor", nullable=False)
    status = Column(String(32), default="COMPLETED", index=True, nullable=False)  # "RUNNING", "COMPLETED", "FAILED"
    total_latency_ms = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)
    trace_steps = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    session = relationship("ShoppingSession", back_populates="agent_runs")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "supervisor_agent": self.supervisor_agent,
            "status": self.status,
            "total_latency_ms": self.total_latency_ms,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "trace_steps": self.trace_steps or [],
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<AgentRun id={self.id} session_id={self.session_id} status={self.status}>"


class AuditEvent(Base):
    """
    Cryptographically chained, immutable audit event record.
    Provides tamper-evident proof for every sensitive policy check, autonomous action, or state change.
    """
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    action = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)  # "PASSED", "STEP_UP_TRIGGERED", "BLOCKED", "SYSTEM_EVENT"
    agent_id = Column(String(64), default="supervisor", nullable=False)
    event_details = Column(JSON, default=dict)
    sha256_hash = Column(String(64), nullable=False, unique=True, index=True)
    prev_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Compound index for sequential audit verification
    __table_args__ = (
        Index("ix_audit_events_created_hash", "created_at", "sha256_hash"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "action": self.action,
            "status": self.status,
            "agent_id": self.agent_id,
            "event_details": self.event_details or {},
            "sha256_hash": self.sha256_hash,
            "prev_hash": self.prev_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<AuditEvent id={self.id} action={self.action} status={self.status}>"


# =====================================================================
# Phase 2: Merchant Marketplace Simulator Domain Models
# =====================================================================

class MerchantModel(Base):
    """Represents a simulated merchant (e.g. Amazon, Flipkart, Croma)."""
    __tablename__ = "merchants"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    merchant_code = Column(String(32), unique=True, nullable=False, index=True)  # "AMAZON", "FLIPKART", "CROMA"
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    capabilities = Column(JSON, default=list, nullable=False)
    rating = Column(Float, default=4.8, nullable=False)
    logo_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    products = relationship("ProductModel", back_populates="merchant", cascade="all, delete-orphan")
    discounts = relationship("DiscountModel", back_populates="merchant", cascade="all, delete-orphan")
    shipping_options = relationship("ShippingOptionModel", back_populates="merchant", cascade="all, delete-orphan")
    carts = relationship("CartModel", back_populates="merchant", cascade="all, delete-orphan")
    orders = relationship("OrderModel", back_populates="merchant", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "merchant_code": self.merchant_code,
            "display_name": self.display_name,
            "description": self.description,
            "is_active": self.is_active,
            "capabilities": self.capabilities or [],
            "rating": self.rating,
            "logo_url": self.logo_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<MerchantModel code={self.merchant_code} name={self.display_name}>"


class ProductModel(Base):
    """Represents a product listed by a merchant in the catalog."""
    __tablename__ = "products"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(64), nullable=False, index=True)
    title = Column(String(512), nullable=False, index=True)
    brand = Column(String(128), nullable=False, index=True)
    category = Column(String(128), nullable=False, index=True)
    model = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    base_price = Column(Numeric(12, 2), nullable=False)
    current_price = Column(Numeric(12, 2), nullable=False, index=True)
    currency = Column(String(10), default="INR", nullable=False)
    rating = Column(Float, default=4.5, nullable=False, index=True)
    review_count = Column(Integer, default=0, nullable=False)
    specs = Column(JSON, default=dict)
    image_url = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    merchant = relationship("MerchantModel", back_populates="products")
    inventory = relationship("InventoryModel", back_populates="product", uselist=False, cascade="all, delete-orphan")
    prices = relationship("PriceModel", back_populates="product", cascade="all, delete-orphan", order_by="PriceModel.valid_from.desc()")

    __table_args__ = (
        Index("ix_products_merchant_category", "merchant_id", "category"),
        Index("ix_products_category_price", "category", "current_price"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "merchant_code": self.merchant.merchant_code if self.merchant else None,
            "merchant_name": self.merchant.display_name if self.merchant else None,
            "sku": self.sku,
            "title": self.title,
            "brand": self.brand,
            "category": self.category,
            "model": self.model,
            "description": self.description,
            "base_price": float(self.base_price) if self.base_price is not None else 0.0,
            "current_price": float(self.current_price) if self.current_price is not None else 0.0,
            "currency": self.currency,
            "rating": self.rating,
            "review_count": self.review_count,
            "specs": self.specs or {},
            "image_url": self.image_url,
            "is_active": self.is_active,
            "inventory_state": self.inventory.availability_state if self.inventory else "IN_STOCK",
            "available_quantity": self.inventory.available_quantity if self.inventory else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<ProductModel id={self.id} sku={self.sku} title={self.title[:30]}>"


class InventoryModel(Base):
    """Tracks stock level, reserved items, and sold count for a product."""
    __tablename__ = "inventory"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    product_id = Column(String(64), ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    available_quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    sold_quantity = Column(Integer, default=0, nullable=False)
    availability_state = Column(String(32), default="IN_STOCK", nullable=False, index=True)  # "IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK"
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationship
    product = relationship("ProductModel", back_populates="inventory")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "merchant_id": self.merchant_id,
            "available_quantity": self.available_quantity,
            "reserved_quantity": self.reserved_quantity,
            "sold_quantity": self.sold_quantity,
            "availability_state": self.availability_state,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<InventoryModel product_id={self.product_id} available={self.available_quantity} state={self.availability_state}>"


class PriceModel(Base):
    """Tracks historical and promotional price revisions for a product."""
    __tablename__ = "prices"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    product_id = Column(String(64), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    base_price = Column(Numeric(12, 2), nullable=False)
    current_price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    valid_from = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationship
    product = relationship("ProductModel", back_populates="prices")


class DiscountModel(Base):
    """Represents a merchant promotion or coupon code."""
    __tablename__ = "discounts"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(64), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    discount_type = Column(String(32), default="PERCENTAGE", nullable=False)  # "PERCENTAGE", "FLAT"
    discount_value = Column(Numeric(12, 2), nullable=False)
    min_order_value = Column(Numeric(12, 2), default=0.0, nullable=False)
    max_discount = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    starts_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    merchant = relationship("MerchantModel", back_populates="discounts")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "code": self.code,
            "description": self.description,
            "discount_type": self.discount_type,
            "discount_value": float(self.discount_value) if self.discount_value is not None else 0.0,
            "min_order_value": float(self.min_order_value) if self.min_order_value is not None else 0.0,
            "max_discount": float(self.max_discount) if self.max_discount is not None else None,
            "is_active": self.is_active,
            "starts_at": self.starts_at.isoformat() if self.starts_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class ShippingOptionModel(Base):
    """Defines shipping methods offered by a merchant."""
    __tablename__ = "shipping_options"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(32), nullable=False, index=True)  # "STANDARD", "EXPRESS", "SAME_DAY", "STORE_PICKUP"
    name = Column(String(128), nullable=False)
    cost = Column(Numeric(12, 2), default=0.0, nullable=False)
    estimated_days = Column(Integer, default=3, nullable=False)
    delivery_type = Column(String(32), default="STANDARD", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationship
    merchant = relationship("MerchantModel", back_populates="shipping_options")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "code": self.code,
            "name": self.name,
            "cost": float(self.cost) if self.cost is not None else 0.0,
            "estimated_days": self.estimated_days,
            "delivery_type": self.delivery_type,
            "is_active": self.is_active
        }


class CartModel(Base):
    """Represents a merchant-scoped shopping cart."""
    __tablename__ = "carts"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    subtotal = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    shipping_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    grand_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False, index=True)  # "ACTIVE", "MERGED", "CHECKED_OUT", "ABANDONED"
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    merchant = relationship("MerchantModel", back_populates="carts")
    items = relationship("CartItemModel", back_populates="cart", cascade="all, delete-orphan", order_by="CartItemModel.created_at")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "merchant_code": self.merchant.merchant_code if self.merchant else None,
            "session_id": self.session_id,
            "items": [item.to_dict() for item in self.items] if self.items else [],
            "items_count": sum(item.quantity for item in self.items) if self.items else 0,
            "subtotal": float(self.subtotal) if self.subtotal is not None else 0.0,
            "discount_total": float(self.discount_total) if self.discount_total is not None else 0.0,
            "shipping_total": float(self.shipping_total) if self.shipping_total is not None else 0.0,
            "tax_total": float(self.tax_total) if self.tax_total is not None else 0.0,
            "grand_total": float(self.grand_total) if self.grand_total is not None else 0.0,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CartItemModel(Base):
    """Represents an item within a merchant cart."""
    __tablename__ = "cart_items"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    cart_id = Column(String(64), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(64), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    cart = relationship("CartModel", back_populates="items")
    product = relationship("ProductModel")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "product_title": self.product.title if self.product else None,
            "sku": self.product.sku if self.product else None,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price is not None else 0.0,
            "total_price": float(self.total_price) if self.total_price is not None else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CheckoutSessionModel(Base):
    """Represents a validated, server-signed pre-checkout calculation session."""
    __tablename__ = "checkout_sessions"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    cart_id = Column(String(64), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    subtotal = Column(Numeric(12, 2), nullable=False)
    discount_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    shipping_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    grand_total = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    shipping_option_id = Column(String(64), nullable=True)
    promo_code = Column(String(64), nullable=True)
    items_snapshot = Column(JSON, default=list)
    status = Column(String(32), default="PENDING", nullable=False, index=True)  # "PENDING", "COMPLETED", "EXPIRED", "CANCELLED"
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "cart_id": self.cart_id,
            "merchant_id": self.merchant_id,
            "session_id": self.session_id,
            "subtotal": float(self.subtotal) if self.subtotal is not None else 0.0,
            "discount_total": float(self.discount_total) if self.discount_total is not None else 0.0,
            "shipping_total": float(self.shipping_total) if self.shipping_total is not None else 0.0,
            "tax_total": float(self.tax_total) if self.tax_total is not None else 0.0,
            "grand_total": float(self.grand_total) if self.grand_total is not None else 0.0,
            "currency": self.currency,
            "shipping_option_id": self.shipping_option_id,
            "promo_code": self.promo_code,
            "items_snapshot": self.items_snapshot or [],
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class OrderModel(Base):
    """Represents a confirmed commerce order placed with a simulated merchant."""
    __tablename__ = "orders"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    order_number = Column(String(64), unique=True, nullable=False, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    subtotal = Column(Numeric(12, 2), nullable=False)
    discount_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    shipping_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    grand_total = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    shipping_address = Column(Text, nullable=False)
    shipping_method = Column(String(64), default="STANDARD", nullable=False)
    payment_method = Column(String(64), default="UPI_SIMULATED", nullable=False)
    status = Column(String(32), default="CREATED", nullable=False, index=True)  # "CREATED", "CONFIRMED", "PROCESSING", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"
    tracking_number = Column(String(64), nullable=True, index=True)
    estimated_delivery = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    merchant = relationship("MerchantModel", back_populates="orders")
    items = relationship("OrderItemModel", back_populates="order", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_number": self.order_number,
            "merchant_id": self.merchant_id,
            "merchant_code": self.merchant.merchant_code if self.merchant else None,
            "merchant_name": self.merchant.display_name if self.merchant else None,
            "session_id": self.session_id,
            "items": [item.to_dict() for item in self.items] if self.items else [],
            "subtotal": float(self.subtotal) if self.subtotal is not None else 0.0,
            "discount_total": float(self.discount_total) if self.discount_total is not None else 0.0,
            "shipping_total": float(self.shipping_total) if self.shipping_total is not None else 0.0,
            "tax_total": float(self.tax_total) if self.tax_total is not None else 0.0,
            "grand_total": float(self.grand_total) if self.grand_total is not None else 0.0,
            "currency": self.currency,
            "shipping_address": self.shipping_address,
            "shipping_method": self.shipping_method,
            "payment_method": self.payment_method,
            "status": self.status,
            "tracking_number": self.tracking_number,
            "estimated_delivery": self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class OrderItemModel(Base):
    """Represents a line item inside a confirmed order."""
    __tablename__ = "order_items"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    order_id = Column(String(64), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(64), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    product_title = Column(String(512), nullable=False)
    sku = Column(String(64), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)

    # Relationship
    order = relationship("OrderModel", back_populates="items")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_title": self.product_title,
            "sku": self.sku,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price is not None else 0.0,
            "total_price": float(self.total_price) if self.total_price is not None else 0.0
        }

