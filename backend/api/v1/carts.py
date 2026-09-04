"""
Phase 2: Shopping Cart API Endpoints
Provides stateful multi-merchant cart manipulation with server-side inventory verification and price recalculation.
"""
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database.session import get_db_session
from backend.domain.marketplace import (
    CartCreateRequest, CartDetail, CartItemCreate, CartItemUpdate,
    RecommendationSelectionRequest, RecommendationSelectionResponse
)
from backend.services.cart_service import CartService
from backend.core.errors import EntityNotFoundException

carts_router = APIRouter(prefix="/carts", tags=["Shopping Carts"])


@carts_router.post(
    "/select",
    response_model=RecommendationSelectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Select Recommended Product into Merchant Cart",
    description="Validates a user-selected recommendation server-side against live catalog price, inventory, and merchant isolation, then mutates the appropriate merchant cart."
)
def select_recommendation_and_add_to_cart(
    request: RecommendationSelectionRequest,
    db: Session = Depends(get_db_session)
) -> RecommendationSelectionResponse:
    return CartService.select_recommendation_and_add_to_cart(db, request)


@carts_router.post(
    "",
    response_model=CartDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create Merchant Cart",
    description="Creates an isolated, stateful cart dedicated to a specific merchant (e.g. Amazon, Flipkart, Croma)."
)
def create_cart(
    request: CartCreateRequest,
    db: Session = Depends(get_db_session)
) -> CartDetail:
    cart = CartService.create_cart(db, request.merchant_code, request.session_id)
    return CartService.to_dto(cart)


@carts_router.get(
    "/{cart_id}",
    response_model=CartDetail,
    summary="Get Cart",
    description="Retrieves cart contents and recalculates item totals, subtotals, and taxes server-side."
)
def get_cart(
    cart_id: str,
    db: Session = Depends(get_db_session)
) -> CartDetail:
    cart = CartService.get_cart(db, cart_id)
    if not cart:
        raise EntityNotFoundException("Cart", cart_id)
    CartService.recalculate_cart(db, cart)
    return CartService.to_dto(cart)


@carts_router.post(
    "/{cart_id}/items",
    response_model=CartDetail,
    summary="Add Item to Cart",
    description="Adds a product to the designated merchant cart, verifying stock availability and merchant isolation."
)
def add_item_to_cart(
    cart_id: str,
    item_req: CartItemCreate,
    db: Session = Depends(get_db_session)
) -> CartDetail:
    cart = CartService.add_item_to_cart(db, cart_id, item_req.product_id, item_req.quantity)
    return CartService.to_dto(cart)


@carts_router.patch(
    "/{cart_id}/items/{item_id}",
    response_model=CartDetail,
    summary="Update Cart Item Quantity",
    description="Modifies item quantity in cart. Setting quantity to 0 removes the line item."
)
def update_cart_item(
    cart_id: str,
    item_id: str,
    update_req: CartItemUpdate,
    db: Session = Depends(get_db_session)
) -> CartDetail:
    cart = CartService.update_cart_item(db, cart_id, item_id, update_req.quantity)
    return CartService.to_dto(cart)


@carts_router.delete(
    "/{cart_id}/items/{item_id}",
    response_model=CartDetail,
    summary="Remove Cart Item",
    description="Removes a specific line item from the shopping cart."
)
def remove_cart_item(
    cart_id: str,
    item_id: str,
    db: Session = Depends(get_db_session)
) -> CartDetail:
    cart = CartService.remove_cart_item(db, cart_id, item_id)
    return CartService.to_dto(cart)


@carts_router.delete(
    "/{cart_id}",
    response_model=CartDetail,
    summary="Clear Cart",
    description="Empties all items from the shopping cart."
)
def clear_cart(
    cart_id: str,
    db: Session = Depends(get_db_session)
) -> CartDetail:
    cart = CartService.clear_cart(db, cart_id)
    return CartService.to_dto(cart)
