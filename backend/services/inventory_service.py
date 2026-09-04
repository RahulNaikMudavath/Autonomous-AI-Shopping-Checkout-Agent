"""
Phase 2: Inventory & Stock Management Service
Handles transactional stock checks, reservations, commits, and availability state computation.
Prevents overselling and negative inventory invariants.
"""
import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from backend.database.models import InventoryModel, ProductModel
from backend.core.errors import AgentCartException

logger = logging.getLogger("agentcart.inventory")


class OutOfStockException(AgentCartException):
    """Raised when an item has zero available inventory."""
    def __init__(self, product_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Product '{product_id}' is currently out of stock.",
            code="OUT_OF_STOCK",
            status_code=400,
            details={"product_id": product_id}
        )


class InsufficientInventoryException(AgentCartException):
    """Raised when requested quantity exceeds available stock."""
    def __init__(self, product_id: str, requested: int, available: int):
        super().__init__(
            message=f"Insufficient inventory for product '{product_id}'. Requested: {requested}, Available: {available}.",
            code="INSUFFICIENT_INVENTORY",
            status_code=400,
            details={"product_id": product_id, "requested": requested, "available": available}
        )


class InventoryService:
    """
    Transactional inventory coordinator.
    """

    @staticmethod
    def compute_state(available: int) -> str:
        """Determines availability state string from available quantity."""
        if available <= 0:
            return "OUT_OF_STOCK"
        elif available <= 5:
            return "LOW_STOCK"
        return "IN_STOCK"

    @classmethod
    def get_or_create_inventory(
        cls,
        db: Session,
        product_id: str,
        merchant_id: str,
        initial_quantity: int = 10
    ) -> InventoryModel:
        """Fetches existing inventory or initializes stock level for a product."""
        inv = db.query(InventoryModel).filter(InventoryModel.product_id == product_id).first()
        if not inv:
            state = cls.compute_state(initial_quantity)
            inv = InventoryModel(
                product_id=product_id,
                merchant_id=merchant_id,
                available_quantity=max(0, initial_quantity),
                reserved_quantity=0,
                sold_quantity=0,
                availability_state=state
            )
            db.add(inv)
            db.commit()
            db.refresh(inv)
        return inv

    @classmethod
    def check_availability(
        cls,
        db: Session,
        product_id: str,
        requested_quantity: int = 1
    ) -> Tuple[bool, int, str]:
        """
        Inspects live inventory level without modifying state.
        Returns: (can_fulfill, available_quantity, availability_state)
        """
        inv = db.query(InventoryModel).filter(InventoryModel.product_id == product_id).first()
        if not inv:
            return False, 0, "OUT_OF_STOCK"

        can_fulfill = (inv.available_quantity >= requested_quantity) and (requested_quantity > 0)
        return can_fulfill, inv.available_quantity, inv.availability_state

    @classmethod
    def reserve_stock(
        cls,
        db: Session,
        product_id: str,
        quantity: int
    ) -> InventoryModel:
        """
        Transactionally reserves stock for a pending checkout session.
        Atomically shifts available_quantity -> reserved_quantity.
        """
        if quantity <= 0:
            raise AgentCartException("Quantity to reserve must be greater than zero.", code="INVALID_QUANTITY", status_code=400)

        inv = db.query(InventoryModel).filter(InventoryModel.product_id == product_id).with_for_update().first()
        if not inv:
            raise OutOfStockException(product_id)

        if inv.available_quantity < quantity:
            if inv.available_quantity == 0:
                raise OutOfStockException(product_id)
            raise InsufficientInventoryException(product_id, quantity, inv.available_quantity)

        inv.available_quantity -= quantity
        inv.reserved_quantity += quantity
        inv.availability_state = cls.compute_state(inv.available_quantity)

        db.flush()
        logger.info("Reserved %d units of product %s. Remaining available: %d", quantity, product_id, inv.available_quantity)
        return inv

    @classmethod
    def release_stock(
        cls,
        db: Session,
        product_id: str,
        quantity: int
    ) -> InventoryModel:
        """
        Releases previously reserved stock back to available pool (e.g. cart cleared or checkout expired).
        """
        inv = db.query(InventoryModel).filter(InventoryModel.product_id == product_id).with_for_update().first()
        if not inv:
            return inv

        actual_release = min(inv.reserved_quantity, quantity)
        inv.reserved_quantity -= actual_release
        inv.available_quantity += actual_release
        inv.availability_state = cls.compute_state(inv.available_quantity)

        db.flush()
        logger.info("Released %d units of product %s. New available: %d", actual_release, product_id, inv.available_quantity)
        return inv

    @classmethod
    def commit_sold_stock(
        cls,
        db: Session,
        product_id: str,
        quantity: int
    ) -> InventoryModel:
        """
        Transitions reserved stock to permanently sold upon confirmed order placement.
        """
        inv = db.query(InventoryModel).filter(InventoryModel.product_id == product_id).with_for_update().first()
        if not inv:
            return inv

        actual_commit = min(inv.reserved_quantity, quantity)
        inv.reserved_quantity -= actual_commit
        inv.sold_quantity += actual_commit

        db.flush()
        logger.info("Committed %d sold units of product %s. Total sold: %d", actual_commit, product_id, inv.sold_quantity)
        return inv
