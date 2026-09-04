"""
Phase 2: Order Lifecycle & Tracking API Endpoints
Provides endpoints to create simulated orders, track delivery progress, and query order histories.
"""
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db_session
from backend.domain.marketplace import (
    OrderCreateRequest, OrderDetail, OrderTrackingResponse
)
from backend.services.order_service import OrderService
from backend.core.errors import EntityNotFoundException

orders_router = APIRouter(prefix="/orders", tags=["Orders & Tracking"])


class OrderStatusUpdateRequest(BaseModel):
    status: str


@orders_router.post(
    "",
    response_model=OrderDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create Simulated Order",
    description="Places a confirmed merchant order using a prepared CheckoutSession. Commits inventory and issues tracking telemetry."
)
def create_order(
    request: OrderCreateRequest,
    db: Session = Depends(get_db_session)
) -> OrderDetail:
    order = OrderService.create_order(db, request)
    return OrderService.to_dto(order)


@orders_router.get(
    "/{order_id_or_number}",
    response_model=OrderDetail,
    summary="Get Order by ID or Number",
    description="Retrieves confirmed order details, itemized line items, and fulfillment state."
)
def get_order(
    order_id_or_number: str,
    db: Session = Depends(get_db_session)
) -> OrderDetail:
    order = OrderService.get_order_by_id(db, order_id_or_number)
    if not order:
        raise EntityNotFoundException("Order", order_id_or_number)
    return OrderService.to_dto(order)


@orders_router.get(
    "/{order_id_or_number}/tracking",
    response_model=OrderTrackingResponse,
    summary="Track Order Fulfillment",
    description="Returns carrier tracking timeline, current transit milestone, and estimated arrival."
)
def track_order(
    order_id_or_number: str,
    db: Session = Depends(get_db_session)
) -> OrderTrackingResponse:
    return OrderService.track_order(db, order_id_or_number)


@orders_router.get(
    "",
    response_model=List[OrderDetail],
    summary="List Orders",
    description="Lists recent orders placed across merchants, with optional session filtering."
)
def list_orders(
    session_id: Optional[str] = Query(None, description="Filter by shopping session ID"),
    db: Session = Depends(get_db_session)
) -> List[OrderDetail]:
    orders = OrderService.list_orders(db, session_id=session_id)
    return [OrderService.to_dto(o) for o in orders]


@orders_router.patch(
    "/{order_id}/status",
    response_model=OrderDetail,
    summary="Update Order Status",
    description="Simulates carrier transit updates (e.g. PROCESSING -> SHIPPED -> DELIVERED)."
)
def update_order_status(
    order_id: str,
    status_req: OrderStatusUpdateRequest,
    db: Session = Depends(get_db_session)
) -> OrderDetail:
    order = OrderService.update_order_status(db, order_id, status_req.status)
    return OrderService.to_dto(order)
