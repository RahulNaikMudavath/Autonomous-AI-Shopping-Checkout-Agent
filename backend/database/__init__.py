"""
AgentCart Database Package
Exposes domain models, session factory, engine initialization, and health check utilities.
"""
from backend.database.models import (
    Base,
    User,
    UserPreference,
    ShoppingSession,
    ShoppingTask,
    AgentRun,
    AuditEvent
)
from backend.database.session import (
    get_engine,
    init_db,
    get_db_session,
    check_db_health,
    reset_db_engine
)

__all__ = [
    "Base",
    "User",
    "UserPreference",
    "ShoppingSession",
    "ShoppingTask",
    "AgentRun",
    "AuditEvent",
    "get_engine",
    "init_db",
    "get_db_session",
    "check_db_health",
    "reset_db_engine"
]
