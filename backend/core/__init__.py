"""
AgentCart Core Package
Contains configuration, structured logging, error handling, and security middleware.
"""
from backend.core.config import AppSettings, get_settings, update_runtime_settings
from backend.core.logging import setup_logging, CorrelationIdMiddleware
from backend.core.errors import (
    AgentCartException,
    EntityNotFoundException,
    ValidationException,
    DatabaseConnectionError,
    RedisConnectionError,
    PolicyViolationError,
    register_exception_handlers,
    create_error_response
)
from backend.core.security import SecurityHeadersMiddleware

__all__ = [
    "AppSettings",
    "get_settings",
    "update_runtime_settings",
    "setup_logging",
    "CorrelationIdMiddleware",
    "AgentCartException",
    "EntityNotFoundException",
    "ValidationException",
    "DatabaseConnectionError",
    "RedisConnectionError",
    "PolicyViolationError",
    "register_exception_handlers",
    "create_error_response",
    "SecurityHeadersMiddleware"
]
