"""
AgentCart API v1 Router Aggregator
Combines health, shopping sessions, tasks, and system architecture endpoints.
"""
from fastapi import APIRouter
from backend.api.v1.health import health_router
from backend.api.v1.sessions import sessions_router
from backend.api.v1.system import system_router

api_v1_router = APIRouter()

# Mount sub-routers under /api/v1
api_v1_router.include_router(health_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(system_router)

__all__ = ["api_v1_router"]
