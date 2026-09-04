"""
AgentCart Domain Schemas & API Data Transfer Objects (Pydantic v2)
Defines strictly typed request and response schemas for all Phase 1 endpoints.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# =====================================================================
# Health & System Status Schemas
# =====================================================================

class ComponentHealth(BaseModel):
    """Health details of an individual subsystem (e.g. Postgres, Redis)."""
    status: str = Field(..., description="Status string: connected | degraded | fallback_active")
    dialect: Optional[str] = Field(default=None, description="Database dialect or driver name")
    mode: Optional[str] = Field(default=None, description="Redis operating mode")
    latency_ms: Optional[float] = Field(default=None, description="Probe response latency in milliseconds")
    healthy: bool = Field(..., description="Boolean flag indicating component operational health")
    error: Optional[str] = Field(default=None, description="Error message if probe failed")

    model_config = ConfigDict(extra="ignore")


class HealthResponse(BaseModel):
    """Liveness probe response model."""
    status: str = Field(default="ok", description="Liveness status")
    version: str = Field(..., description="AgentCart API version")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")

    model_config = ConfigDict(extra="ignore")


class ReadinessResponse(BaseModel):
    """Readiness probe response model including dependency health."""
    status: str = Field(..., description="Overall readiness: READY | DEGRADED | NOT_READY")
    version: str = Field(..., description="AgentCart API version")
    environment: str = Field(..., description="Runtime environment")
    database: ComponentHealth = Field(..., description="PostgreSQL health telemetry")
    redis: ComponentHealth = Field(..., description="Redis cache and state health telemetry")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")

    model_config = ConfigDict(extra="ignore")


class ArchitectureLayerInfo(BaseModel):
    """Metadata describing one of the 9 foundational architectural layers."""
    layer_number: int
    name: str
    boundary_responsibility: str
    isolation_rationale: str
    status: str = "active"


class SystemInfoResponse(BaseModel):
    """Comprehensive system and architecture information."""
    app_name: str
    version: str
    environment: str
    api_v1_prefix: str
    layers: List[ArchitectureLayerInfo]
    database_status: str
    redis_status: str
    timestamp: str


# =====================================================================
# User & Preference Schemas
# =====================================================================

class UserCreate(BaseModel):
    """Schema for registering a new user."""
    email: str = Field(..., min_length=5, max_length=255, description="Valid user email address")
    name: str = Field(..., min_length=1, max_length=255, description="User full name")


class UserResponse(BaseModel):
    """Schema representing user data returned by the API."""
    id: str
    email: str
    name: str
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserPreferenceCreate(BaseModel):
    """Schema for creating or updating user preferences."""
    user_id: str
    brand_affinity: Optional[List[str]] = Field(default_factory=list)
    price_sensitivity: Optional[str] = Field(default="balanced")
    default_shipping_address: Optional[str] = None
    default_currency: Optional[str] = Field(default="INR")
    max_auto_approval_budget: Optional[float] = Field(default=5000.0)


class UserPreferenceResponse(BaseModel):
    """Schema returning user preferences."""
    id: str
    user_id: str
    brand_affinity: List[str]
    price_sensitivity: str
    default_shipping_address: Optional[str]
    default_currency: str
    max_auto_approval_budget: float
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# Shopping Session Schemas
# =====================================================================

class ShoppingSessionCreate(BaseModel):
    """Request payload to create a new shopping session."""
    user_id: str = Field(..., description="ID of the user initiating the session")
    title: Optional[str] = Field(default="New Shopping Session", max_length=255, description="Session title or intent summary")
    session_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata tags or client info")


class ShoppingSessionUpdate(BaseModel):
    """Request payload to update an existing shopping session."""
    title: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = Field(default=None, description="ACTIVE | COMPLETED | ABORTED")
    session_metadata: Optional[Dict[str, Any]] = None


class ShoppingSessionResponse(BaseModel):
    """Schema returning detailed shopping session status."""
    id: str
    user_id: str
    title: str
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tasks_count: int = 0
    agent_runs_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# Shopping Task Schemas
# =====================================================================

class ShoppingTaskCreate(BaseModel):
    """Request payload to add a discrete shopping goal or prompt to a session."""
    raw_prompt: str = Field(..., min_length=3, description="User's natural language shopping request")
    extracted_constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)
    execution_plan: Optional[List[Any]] = Field(default_factory=list)


class ShoppingTaskResponse(BaseModel):
    """Schema returning shopping task details."""
    id: str
    session_id: str
    raw_prompt: str
    status: str
    extracted_constraints: Dict[str, Any] = Field(default_factory=dict)
    execution_plan: List[Any] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# Agent Run & Audit Event Schemas
# =====================================================================

class AgentRunResponse(BaseModel):
    """Schema returning multi-agent execution telemetry."""
    id: str
    session_id: str
    supervisor_agent: str
    status: str
    total_latency_ms: int
    total_tokens: int
    estimated_cost_usd: float
    trace_steps: List[Any] = Field(default_factory=list)
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuditEventResponse(BaseModel):
    """Schema returning tamper-evident audit ledger entries."""
    id: str
    session_id: Optional[str]
    action: str
    status: str
    agent_id: str
    event_details: Dict[str, Any] = Field(default_factory=dict)
    sha256_hash: str
    prev_hash: str
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
