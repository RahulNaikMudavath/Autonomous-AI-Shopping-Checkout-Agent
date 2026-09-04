"""
AgentCart System Information & Architecture Metadata API (v1)
Exposes machine-readable architecture layers and service boundary definitions.
"""
from datetime import datetime, timezone
from fastapi import APIRouter
from backend.core.config import get_settings
from backend.database.session import check_db_health
from backend.services.redis_service import get_redis_service
from backend.domain.schemas import SystemInfoResponse, ArchitectureLayerInfo

system_router = APIRouter(prefix="/system", tags=["System & Architecture"])

ARCHITECTURE_LAYERS = [
    ArchitectureLayerInfo(
        layer_number=1,
        name="Presentation & User Experience Layer",
        boundary_responsibility="Manages client interfaces, conversational input, real-time WebSocket state streaming, and human-in-the-loop confirmations.",
        isolation_rationale="Decouples frontend rendering from backend business logic and AI reasoning workflows.",
        status="active"
    ),
    ArchitectureLayerInfo(
        layer_number=2,
        name="API Gateway & Security Layer",
        boundary_responsibility="Handles routing, versioning (/api/v1), CORS, correlation ID tracing, OWASP security headers, and rate limiting.",
        isolation_rationale="Acts as the single point of entry, protecting internal microservices and domain logic from unauthenticated/malformed traffic.",
        status="active"
    ),
    ArchitectureLayerInfo(
        layer_number=3,
        name="Agent Intelligence Layer",
        boundary_responsibility="Orchestrates hierarchical multi-agent supervisor, intent extraction, multi-step planning, discovery, and ranking.",
        isolation_rationale="Isolates non-deterministic LLM reasoning from deterministic business and financial state transitions.",
        status="scaffolded"
    ),
    ArchitectureLayerInfo(
        layer_number=4,
        name="Trust, Safety & Policy Engine Layer",
        boundary_responsibility="Enforces spending limits, merchant whitelists, prompt injection sanitization, step-up authentication, and immutable audit logs.",
        isolation_rationale="Guarantees hard safety constraints that cannot be bypassed by agent hallucination or prompt injection.",
        status="active"
    ),
    ArchitectureLayerInfo(
        layer_number=5,
        name="Universal Commerce & Merchant Abstraction Layer",
        boundary_responsibility="Standardizes product discovery, catalog schema mapping, and unified cart manipulation across diverse merchants.",
        isolation_rationale="Prevents vendor lock-in by encapsulating merchant-specific REST/GraphQL/MCP APIs behind a single protocol.",
        status="active"
    ),
    ArchitectureLayerInfo(
        layer_number=6,
        name="Payment Abstraction & Delegated Auth Layer",
        boundary_responsibility="Manages tokenized payment mandates, virtual cards, escrow holds, and cryptographic checkout verification.",
        isolation_rationale="PCI-DSS compliance and financial risk isolation: agents never access raw PAN/CVV or unconstrained payment credentials.",
        status="active"
    ),
    ArchitectureLayerInfo(
        layer_number=7,
        name="Durable Data & Domain Storage Layer",
        boundary_responsibility="Persists relational records (Users, Preferences, Sessions, Tasks, Runs, Chained Audit Ledger) in PostgreSQL.",
        isolation_rationale="Provides ACID transactions, relational integrity, and long-term historical records.",
        status="active"
    ),
    ArchitectureLayerInfo(
        layer_number=8,
        name="Ephemeral State & Distributed Cache Layer",
        boundary_responsibility="Manages fast in-memory agent working memory, task scratchpads, session TTL locks, and response caching in Redis.",
        isolation_rationale="Low-latency volatile storage that offloads read load from PostgreSQL and enables stateless backend instances.",
        status="active"
    ),
    ArchitectureLayerInfo(
        layer_number=9,
        name="Observability, Telemetry & Evaluation Layer",
        boundary_responsibility="Captures structured JSON access logs, OpenTelemetry traces, Langfuse LLM tokens/costs, and benchmark evaluation runs.",
        isolation_rationale="Provides real-time visibility and auditability into agent behavior without impacting core request latency.",
        status="active"
    ),
]


@system_router.get(
    "/info",
    response_model=SystemInfoResponse,
    summary="System Architecture & Metadata",
    description="Returns detailed information about AgentCart's 9 architectural layers, service boundaries, and runtime status."
)
async def get_system_info():
    settings = get_settings()
    db_res = check_db_health()
    redis_service = get_redis_service()
    redis_res = redis_service.check_redis_health()

    return SystemInfoResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        api_v1_prefix=settings.api_v1_prefix,
        layers=ARCHITECTURE_LAYERS,
        database_status=db_res.get("status", "unknown"),
        redis_status=redis_res.get("status", "unknown"),
        timestamp=datetime.now(timezone.utc).isoformat()
    )
