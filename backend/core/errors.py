"""
AgentCart Error Handling & RFC 7807 Error Envelopes
Defines the domain exception hierarchy and global FastAPI exception handlers.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("agentcart.errors")


# =====================================================================
# Domain Exceptions Hierarchy
# =====================================================================

class AgentCartException(Exception):
    """Base exception for all AgentCart domain and application errors."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class EntityNotFoundException(AgentCartException):
    """Raised when a requested resource (session, task, user, order) does not exist."""
    def __init__(self, entity_name: str, entity_id: str, message: Optional[str] = None):
        msg = message or f"{entity_name} with ID '{entity_id}' was not found."
        super().__init__(
            message=msg,
            code="ENTITY_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"entity_name": entity_name, "entity_id": entity_id}
        )


class ValidationException(AgentCartException):
    """Raised when business logic or input validation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details or {}
        )


class DatabaseConnectionError(AgentCartException):
    """Raised when database connectivity fails."""
    def __init__(self, message: str = "Database connection unavailable"):
        super().__init__(
            message=message,
            code="DATABASE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class RedisConnectionError(AgentCartException):
    """Raised when Redis connectivity fails."""
    def __init__(self, message: str = "Redis cache unavailable"):
        super().__init__(
            message=message,
            code="REDIS_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class PolicyViolationError(AgentCartException):
    """Raised when an operation violates trust & safety or spending policies."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="POLICY_VIOLATION",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details or {}
        )


# =====================================================================
# Standard Error Envelope Formatter
# =====================================================================

def create_error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Builds a standard, RFC 7807-inspired JSON error payload."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    error_payload = {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
            "request_id": request_id,
        }
    }
    
    return JSONResponse(
        status_code=status_code,
        content=error_payload,
        headers={"X-Request-ID": request_id}
    )


# =====================================================================
# Global Exception Handlers
# =====================================================================

def register_exception_handlers(app: FastAPI) -> None:
    """Registers unified exception handlers onto the FastAPI application."""

    @app.exception_handler(AgentCartException)
    async def agentcart_exception_handler(request: Request, exc: AgentCartException):
        logger.warning(
            "AgentCartException: code=%s, status=%d, msg=%s",
            exc.code, exc.status_code, exc.message
        )
        return create_error_response(
            request=request,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            422: "UNPROCESSABLE_ENTITY",
            500: "INTERNAL_SERVER_ERROR",
            503: "SERVICE_UNAVAILABLE"
        }
        code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
        message = exc.detail if isinstance(exc.detail, str) else "HTTP Exception occurred."
        details = exc.detail if isinstance(exc.detail, dict) else {}

        return create_error_response(
            request=request,
            status_code=exc.status_code,
            code=code,
            message=message,
            details=details
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.info("Request validation failed: %s", exc.errors())
        # Format Pydantic errors cleanly
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            errors.append({"field": loc, "message": err.get("msg"), "type": err.get("type")})

        return create_error_response(
            request=request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="REQUEST_VALIDATION_FAILED",
            message="Invalid request body or parameters.",
            details={"validation_errors": errors}
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled server exception on %s %s: %s", request.method, request.url.path, str(exc))
        return create_error_response(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred. Please try again later.",
            details={"error_class": exc.__class__.__name__}
        )
