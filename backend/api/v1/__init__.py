"""
AgentCart API v1 Router Aggregator
Combines health, shopping sessions, tasks, and system architecture endpoints.
"""
from fastapi import APIRouter
from backend.api.v1.health import health_router
from backend.api.v1.sessions import sessions_router
from backend.api.v1.system import system_router
from backend.api.v1.merchants import merchants_router
from backend.api.v1.products import products_router
from backend.api.v1.carts import carts_router
from backend.api.v1.checkout import checkout_router
from backend.api.v1.orders import orders_router
from backend.api.v1.agent import agent_router

api_v1_router = APIRouter()

# Mount sub-routers under /api/v1
api_v1_router.include_router(health_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(system_router)
api_v1_router.include_router(merchants_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(carts_router)
api_v1_router.include_router(checkout_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(agent_router)

__all__ = ["api_v1_router"]

