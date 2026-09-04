"""
AgentCart Health & Readiness API Endpoints (v1)
Provides lightweight liveness checks and comprehensive readiness probes for container orchestrators.
"""
from datetime import datetime, timezone
import logging
from fastapi import APIRouter, status, Response
from backend.core.config import get_settings
from backend.database.session import check_db_health
from backend.services.redis_service import get_redis_service
from backend.domain.schemas import HealthResponse, ReadinessResponse, ComponentHealth

logger = logging.getLogger("agentcart.api.health")

health_router = APIRouter(tags=["Health & Telemetry"])


@health_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness Probe",
    description="Quick liveness check confirming the HTTP API server is accepting requests."
)
async def get_health():
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@health_router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description="Probes PostgreSQL database and Redis connectivity to verify service readiness."
)
async def get_readiness(response: Response):
    settings = get_settings()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # 1. Probe Database Health
    db_res = check_db_health()
    db_health = ComponentHealth(
        status=db_res.get("status", "unknown"),
        dialect=db_res.get("dialect"),
        latency_ms=db_res.get("latency_ms"),
        healthy=db_res.get("healthy", False),
        error=db_res.get("error")
    )
    
    # 2. Probe Redis Health
    redis_service = get_redis_service()
    redis_res = redis_service.check_redis_health()
    redis_health = ComponentHealth(
        status=redis_res.get("status", "unknown"),
        mode=redis_res.get("mode"),
        latency_ms=redis_res.get("latency_ms"),
        healthy=redis_res.get("healthy", False),
        error=redis_res.get("error")
    )

    # Determine overall status
    is_fully_ready = db_health.healthy and redis_health.healthy
    overall_status = "READY" if is_fully_ready else "DEGRADED"

    if not is_fully_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.environment,
        database=db_health,
        redis=redis_health,
        timestamp=now_iso
    )
