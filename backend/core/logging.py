"""
AgentCart Structured Logging Module
Provides JSON and console formatting, log level control,
and correlation ID tracing middleware for end-to-end request observability.
"""
import logging
import json
import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable for request correlation ID
_correlation_id_ctx = None


class JSONLogFormatter(logging.Formatter):
    """Formats log records as structured JSON for log aggregators (e.g. Datadog, CloudWatch, OpenTelemetry)."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        # Add correlation ID if present in extra or context
        if hasattr(record, "correlation_id") and record.correlation_id:
            log_obj["correlation_id"] = record.correlation_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging(level: str = "INFO", json_format: bool = False) -> logging.Logger:
    """Configures application-wide root and agentcart loggers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    if json_format:
        console_handler.setFormatter(JSONLogFormatter())
    else:
        standard_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(standard_formatter)

    root_logger.addHandler(console_handler)
    
    app_logger = logging.getLogger("agentcart")
    app_logger.info("Structured logging initialized (level=%s, json=%s)", level, json_format)
    return app_logger


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts or generates an 'X-Request-ID' header for every HTTP request,
    attaching it to the response headers and measuring total request execution latency.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate correlation ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()
        
        # Process request
        response = await call_next(request)
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Inject correlation ID and latency into response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-MS"] = f"{latency_ms:.2f}"
        
        # Log request if not a lightweight health probe
        if not request.url.path.endswith("/health"):
            logger = logging.getLogger("agentcart.access")
            logger.info(
                "%s %s -> %d (%.2fms) [req_id=%s]",
                request.method,
                request.url.path,
                response.status_code,
                latency_ms,
                request_id
            )

        return response
