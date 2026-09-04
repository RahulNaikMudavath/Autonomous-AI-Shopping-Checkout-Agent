"""
AgentCart Main Application Entrypoint
FastAPI server implementing the 9-layer autonomous commerce architecture:
- Layer 1: Presentation & User Experience (FastAPI REST & WebSocket endpoints)
- Layer 2: API Gateway, Correlation ID Middleware & OWASP Security Headers
- Layer 3: Agent Intelligence & Context Orchestration
- Layer 4: Trust & Safety Guardrails & Cryptographic Audit Ledger
- Layer 5: Universal Commerce Protocol (UCP) & Merchant Adapters
- Layer 6: Payment Abstraction & Delegated Authorization Sandbox
- Layer 7: Durable PostgreSQL Domain Storage & SQLAlchemy 2.0 ORM
- Layer 8: Redis Ephemeral Memory & Distributed Caching
- Layer 9: Structured Logging, Telemetry & OpenTelemetry Hooks
"""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.core.logging import setup_logging, CorrelationIdMiddleware
from backend.core.security import SecurityHeadersMiddleware
from backend.core.errors import register_exception_handlers
from backend.database.session import init_db
from backend.services.redis_service import get_redis_service
from backend.api.v1 import api_v1_router
from backend.api.v1.health import health_router

# Optional Subsystem Routers (Gracefully imported if available)
try:
    from backend.protocol.ucp import ucp_router
except ImportError:
    ucp_router = None

try:
    from backend.protocol.gateway_router import gateway_router
except ImportError:
    gateway_router = None

try:
    from backend.infrastructure.merchant_apis import merchant_apis_router
except ImportError:
    merchant_apis_router = None

try:
    from backend.infrastructure.merchant_simulator import merchant_sim_router
except ImportError:
    merchant_sim_router = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Executes startup initialization (logging, database tables, redis probe)
    and graceful shutdown teardown.
    """
    settings = get_settings()
    
    # 1. Initialize structured logging
    setup_logging(level="DEBUG" if settings.debug else "INFO", json_format=(settings.environment == "production"))
    logger = logging.getLogger("agentcart.main")
    logger.info("Starting %s v%s (environment: %s)", settings.app_name, settings.app_version, settings.environment)

    # 2. Initialize database schema
    try:
        init_db()
        logger.info("Database schema initialized and verified.")
    except Exception as e:
        logger.error("Database initialization failed: %s", str(e))

    # 3. Probe Redis connection
    redis_service = get_redis_service()
    redis_health = redis_service.check_redis_health()
    logger.info("Redis cache initialized: %s (mode: %s)", redis_health.get("status"), redis_health.get("mode"))

    yield  # Application serves requests

    # Teardown logic on shutdown
    logger.info("Shutting down %s...", settings.app_name)


def create_app() -> FastAPI:
    """Factory function creating and configuring the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AgentCart - Autonomous AI Shopping & Checkout Agent",
        description=(
            "Production-grade 9-Layer Autonomous AI Commerce Architecture "
            "with Trust & Safety Guardrails, Cryptographic Audit Ledger, "
            "Universal Commerce Protocol (UCP), and PostgreSQL/Redis foundation."
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # 1. Register Middlewares (Order: Security Headers -> CORS -> Correlation ID)
    app.add_middleware(SecurityHeadersMiddleware)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time-MS"]
    )
    
    app.add_middleware(CorrelationIdMiddleware)

    # 2. Register Global RFC 7807 Exception Handlers
    register_exception_handlers(app)

    # 3. Mount Primary API Routers (API v1)
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    
    # 4. Root alias health routes (for load balancers & Kubernetes probes)
    app.include_router(health_router, prefix="")

    # 5. Mount Subsystem Routers if present
    if ucp_router:
        app.include_router(ucp_router)
    if gateway_router:
        app.include_router(gateway_router)
    if merchant_apis_router:
        app.include_router(merchant_apis_router)
    if merchant_sim_router:
        app.include_router(merchant_sim_router)

    return app


# Application Instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
