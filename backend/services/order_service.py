"""
Phase 2: Order Management & Tracking Service
Creates simulated orders from validated CheckoutSessions, manages line items, and enforces deterministic state machine transitions.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload

from backend.database.models import (
    OrderModel, OrderItemModel, CheckoutSessionModel, CartModel,
    MerchantModel, ShippingOptionModel
)
from backend.domain.marketplace import (
    OrderCreateRequest, OrderDetail, OrderItemDetail, OrderTrackingResponse, OrderStatus
)
from backend.services.pricing_service import quantize_money, ZERO
from backend.services.inventory_service import InventoryService
from backend.core.errors import AgentCartException, EntityNotFoundException

logger = logging.getLogger("agentcart.orders")

# Valid state machine transitions
ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "CREATED": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["PROCESSING", "CANCELLED"],
    "PROCESSING": ["SHIPPED", "CANCELLED"],
    "SHIPPED": ["OUT_FOR_DELIVERY"],
    "OUT_FOR_DELIVERY": ["DELIVERED"],
    "DELIVERED": [],
    "CANCELLED": []
}


class InvalidOrderStateException(AgentCartException):
    """Raised when an order status transition violates the state machine."""
    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            message=f"Invalid order status transition from '{current_status}' to '{target_status}'.",
            code="INVALID_ORDER_STATE",
            status_code=400,
            details={"current_status": current_status, "target_status": target_status}
        )


class OrderService:
    """
    Coordinates order placement, state transitions, and tracking milestones.
    """

    @classmethod
    def create_order(cls, db: Session, request: OrderCreateRequest) -> OrderModel:
        """
        Transforms a validated CheckoutSession into a confirmed merchant Order.
        Commits inventory reduction, marks cart as checked out, and generates tracking telemetry.
        """
        checkout = db.query(CheckoutSessionModel).filter(
            CheckoutSessionModel.id == request.checkout_session_id
        ).first()

        if not checkout:
            raise EntityNotFoundException("CheckoutSession", request.checkout_session_id)

        now = datetime.now(timezone.utc)
        if checkout.status != "PENDING":
            raise AgentCartException(
                f"Checkout session is already in '{checkout.status}' state.",
                code="CHECKOUT_INVALID_STATE",
                status_code=400
            )

        if checkout.expires_at < now:
            checkout.status = "EXPIRED"
            db.commit()
            raise AgentCartException(
                "Checkout session has expired. Please prepare checkout again.",
                code="CHECKOUT_EXPIRED",
                status_code=400
            )

        merchant = db.query(MerchantModel).filter(MerchantModel.id == checkout.merchant_id).first()
        if not merchant:
            raise EntityNotFoundException("Merchant", checkout.merchant_id)

        # 1. Commit inventory reductions
        for it in (checkout.items_snapshot or []):
            product_id = it.get("product_id")
            qty = int(it.get("quantity", 1))
            InventoryService.commit_sold_stock(db, product_id, qty)

        # 2. Shipping option and ETA
        shipping_method_name = "STANDARD"
        delivery_days = 3
        if checkout.shipping_option_id:
            opt = db.query(ShippingOptionModel).filter(ShippingOptionModel.id == checkout.shipping_option_id).first()
            if opt:
                shipping_method_name = opt.name
                delivery_days = opt.estimated_days

        eta = now + timedelta(days=delivery_days)
        prefix = merchant.merchant_code[:3].upper()
        order_number = f"ORD-{prefix}-{uuid.uuid4().hex[:6].upper()}"
        tracking_number = f"TRK-{prefix}-{uuid.uuid4().hex[:8].upper()}"

        # 3. Create Order
        order = OrderModel(
            order_number=order_number,
            merchant_id=merchant.id,
            session_id=checkout.session_id,
            subtotal=quantize_money(checkout.subtotal),
            discount_total=quantize_money(checkout.discount_total),
            shipping_total=quantize_money(checkout.shipping_total),
            tax_total=quantize_money(checkout.tax_total),
            grand_total=quantize_money(checkout.grand_total),
            currency=checkout.currency,
            shipping_address=request.shipping_address,
            shipping_method=shipping_method_name,
            payment_method=request.payment_method,
            status="CONFIRMED",
            tracking_number=tracking_number,
            estimated_delivery=eta,
            created_at=now,
            updated_at=now
        )
        db.add(order)
        db.flush()

        # 4. Create Order Items
        for it in (checkout.items_snapshot or []):
            u_p = Decimal(str(it.get("unit_price", "0.00")))
            t_p = Decimal(str(it.get("total_price", "0.00")))
            order_item = OrderItemModel(
                order_id=order.id,
                product_id=it.get("product_id"),
                product_title=it.get("product_title", "Product"),
                sku=it.get("sku", "SKU"),
                quantity=int(it.get("quantity", 1)),
                unit_price=quantize_money(u_p),
                total_price=quantize_money(t_p)
            )
            db.add(order_item)

        # 5. Update checkout & cart status
        checkout.status = "COMPLETED"
        cart = db.query(CartModel).filter(CartModel.id == checkout.cart_id).first()
        if cart:
            cart.status = "CHECKED_OUT"

        db.commit()
        db.refresh(order)
        logger.info("Order %s successfully placed with merchant %s", order.order_number, merchant.merchant_code)
        return order

    @classmethod
    def get_order_by_id(cls, db: Session, order_id_or_number: str) -> Optional[OrderModel]:
        """Fetches order by UUID or order_number."""
        return db.query(OrderModel).options(
            joinedload(OrderModel.merchant),
            joinedload(OrderModel.items)
        ).filter(
            (OrderModel.id == order_id_or_number) |
            (OrderModel.order_number == order_id_or_number)
        ).first()

    @classmethod
    def list_orders(
        cls,
        db: Session,
        merchant_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[OrderModel]:
        """Lists orders filtered by merchant or shopping session."""
        query = db.query(OrderModel).options(
            joinedload(OrderModel.merchant),
            joinedload(OrderModel.items)
        )
        if merchant_id:
            query = query.filter(OrderModel.merchant_id == merchant_id)
        if session_id:
            query = query.filter(OrderModel.session_id == session_id)
        return query.order_by(OrderModel.created_at.desc()).all()

    @classmethod
    def update_order_status(cls, db: Session, order_id: str, new_status: str) -> OrderModel:
        """
        Applies a validated state transition to an existing order.
        """
        target_status = new_status.strip().upper()
        order = cls.get_order_by_id(db, order_id)
        if not order:
            raise EntityNotFoundException("Order", order_id)

        curr_status = order.status
        allowed = ALLOWED_TRANSITIONS.get(curr_status, [])
        if target_status not in allowed:
            raise InvalidOrderStateException(curr_status, target_status)

        order.status = target_status
        order.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(order)
        logger.info("Order %s status updated: %s -> %s", order.order_number, curr_status, target_status)
        return order

    @classmethod
    def track_order(cls, db: Session, order_id_or_number: str) -> OrderTrackingResponse:
        """Constructs detailed tracking timeline for an order."""
        order = cls.get_order_by_id(db, order_id_or_number)
        if not order:
            raise EntityNotFoundException("Order", order_id_or_number)

        timeline = [
            {
                "status": "CREATED",
                "label": "Order Created",
                "timestamp": order.created_at.isoformat(),
                "completed": True
            },
            {
                "status": "CONFIRMED",
                "label": "Merchant Confirmed",
                "timestamp": order.created_at.isoformat(),
                "completed": order.status in ["CONFIRMED", "PROCESSING", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"]
            },
            {
                "status": "PROCESSING",
                "label": "Fulfillment & Packing",
                "timestamp": (order.created_at + timedelta(hours=2)).isoformat() if order.status in ["PROCESSING", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"] else None,
                "completed": order.status in ["PROCESSING", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"]
            },
            {
                "status": "SHIPPED",
                "label": "Dispatched with Carrier",
                "timestamp": (order.created_at + timedelta(hours=6)).isoformat() if order.status in ["SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"] else None,
                "completed": order.status in ["SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"]
            },
            {
                "status": "OUT_FOR_DELIVERY",
                "label": "Out for Delivery",
                "timestamp": (order.created_at + timedelta(hours=24)).isoformat() if order.status in ["OUT_FOR_DELIVERY", "DELIVERED"] else None,
                "completed": order.status in ["OUT_FOR_DELIVERY", "DELIVERED"]
            },
            {
                "status": "DELIVERED",
                "label": "Delivered to Customer",
                "timestamp": order.estimated_delivery.isoformat() if order.status == "DELIVERED" and order.estimated_delivery else None,
                "completed": order.status == "DELIVERED"
            }
        ]

        if order.status == "CANCELLED":
            timeline.append({
                "status": "CANCELLED",
                "label": "Order Cancelled",
                "timestamp": order.updated_at.isoformat(),
                "completed": True
            })

        return OrderTrackingResponse(
            order_id=order.id,
            order_number=order.order_number,
            merchant_code=order.merchant.merchant_code if order.merchant else "MERCHANT",
            status=OrderStatus(order.status),
            tracking_number=order.tracking_number,
            carrier=f"{order.merchant.display_name if order.merchant else 'Merchant'} Express Logistics",
            estimated_delivery=order.estimated_delivery.isoformat() if order.estimated_delivery else None,
            status_timeline=timeline,
            shipping_address=order.shipping_address
        )

    @classmethod
    def to_dto(cls, order: OrderModel) -> OrderDetail:
        """Converts OrderModel into validated OrderDetail DTO."""
        items_dto = [
            OrderItemDetail(
                id=it.id,
                product_id=it.product_id,
                product_title=it.product_title,
                sku=it.sku,
                quantity=it.quantity,
                unit_price=quantize_money(it.unit_price),
                total_price=quantize_money(it.total_price)
            )
            for it in order.items
        ]

        return OrderDetail(
            id=order.id,
            order_number=order.order_number,
            merchant_id=order.merchant_id,
            merchant_code=order.merchant.merchant_code if order.merchant else None,
            merchant_name=order.merchant.display_name if order.merchant else None,
            session_id=order.session_id,
            items=items_dto,
            subtotal=quantize_money(order.subtotal),
            discount_total=quantize_money(order.discount_total),
            shipping_total=quantize_money(order.shipping_total),
            tax_total=quantize_money(order.tax_total),
            grand_total=quantize_money(order.grand_total),
            currency=order.currency,
            shipping_address=order.shipping_address,
            shipping_method=order.shipping_method,
            payment_method=order.payment_method,
            status=OrderStatus(order.status),
            tracking_number=order.tracking_number,
            estimated_delivery=order.estimated_delivery.isoformat() if order.estimated_delivery else None,
            created_at=order.created_at.isoformat() if order.created_at else None,
            updated_at=order.updated_at.isoformat() if order.updated_at else None
        )
