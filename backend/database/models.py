"""
AgentCart Database Domain Models (PostgreSQL / SQLAlchemy 2.0)
Defines foundational domain entities for Phase 1:
- User: Core user identity and account state
- UserPreference: Personalization, shipping constraints, budget/brand affinity
- ShoppingSession: Top-level conversation & shopping lifecycle container
- ShoppingTask: Structured discrete intent, requirements, and execution plan
- AgentRun: Execution telemetry, latency, token consumption, cost, and traces
- AuditEvent: Cryptographically chained tamper-evident compliance ledger
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    """Generates a UUID4 string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Returns current UTC timestamp."""
    return datetime.now(timezone.utc)


class User(Base):
    """Represents an authenticated user in the AgentCart system."""
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("ShoppingSession", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class UserPreference(Base):
    """Represents personalized shopping constraints and affinities for a user."""
    __tablename__ = "user_preferences"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    brand_affinity = Column(JSON, default=list)  # e.g. ["Apple", "Sony", "Dell"]
    price_sensitivity = Column(String(32), default="balanced")  # "low", "balanced", "value", "premium"
    default_shipping_address = Column(Text, nullable=True)
    default_currency = Column(String(10), default="INR")
    max_auto_approval_budget = Column(Float, default=5000.0)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="preferences")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "brand_affinity": self.brand_affinity or [],
            "price_sensitivity": self.price_sensitivity,
            "default_shipping_address": self.default_shipping_address,
            "default_currency": self.default_currency,
            "max_auto_approval_budget": self.max_auto_approval_budget,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<UserPreference id={self.id} user_id={self.user_id}>"


class ShoppingSession(Base):
    """Represents a high-level shopping session holding one or more tasks and agent runs."""
    __tablename__ = "shopping_sessions"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Shopping Session", nullable=False)
    status = Column(String(32), default="ACTIVE", index=True, nullable=False)  # "ACTIVE", "COMPLETED", "ABORTED"
    session_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")
    tasks = relationship("ShoppingTask", back_populates="session", cascade="all, delete-orphan", order_by="ShoppingTask.created_at")
    agent_runs = relationship("AgentRun", back_populates="session", cascade="all, delete-orphan", order_by="AgentRun.created_at")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "status": self.status,
            "metadata": self.session_metadata or {},
            "tasks_count": len(self.tasks) if self.tasks else 0,
            "agent_runs_count": len(self.agent_runs) if self.agent_runs else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<ShoppingSession id={self.id} status={self.status}>"


class ShoppingTask(Base):
    """Represents a discrete shopping goal or parsed user query within a session."""
    __tablename__ = "shopping_tasks"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(64), ForeignKey("shopping_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_prompt = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING", index=True, nullable=False)  # "PENDING", "PLANNING", "DISCOVERING", "COMPLETED", "FAILED"
    extracted_constraints = Column(JSON, default=dict)
    execution_plan = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    session = relationship("ShoppingSession", back_populates="tasks")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "raw_prompt": self.raw_prompt,
            "status": self.status,
            "extracted_constraints": self.extracted_constraints or {},
            "execution_plan": self.execution_plan or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<ShoppingTask id={self.id} session_id={self.session_id} status={self.status}>"


class AgentRun(Base):
    """Tracks autonomous multi-agent execution telemetry, latency, token usage, and trace steps."""
    __tablename__ = "agent_runs"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(64), ForeignKey("shopping_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    supervisor_agent = Column(String(64), default="LangGraphSupervisor", nullable=False)
    status = Column(String(32), default="COMPLETED", index=True, nullable=False)  # "RUNNING", "COMPLETED", "FAILED"
    total_latency_ms = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)
    trace_steps = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    session = relationship("ShoppingSession", back_populates="agent_runs")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "supervisor_agent": self.supervisor_agent,
            "status": self.status,
            "total_latency_ms": self.total_latency_ms,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "trace_steps": self.trace_steps or [],
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<AgentRun id={self.id} session_id={self.session_id} status={self.status}>"


class AuditEvent(Base):
    """
    Cryptographically chained, immutable audit event record.
    Provides tamper-evident proof for every sensitive policy check, autonomous action, or state change.
    """
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    action = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)  # "PASSED", "STEP_UP_TRIGGERED", "BLOCKED", "SYSTEM_EVENT"
    agent_id = Column(String(64), default="supervisor", nullable=False)
    event_details = Column(JSON, default=dict)
    sha256_hash = Column(String(64), nullable=False, unique=True, index=True)
    prev_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Compound index for sequential audit verification
    __table_args__ = (
        Index("ix_audit_events_created_hash", "created_at", "sha256_hash"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "action": self.action,
            "status": self.status,
            "agent_id": self.agent_id,
            "event_details": self.event_details or {},
            "sha256_hash": self.sha256_hash,
            "prev_hash": self.prev_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<AuditEvent id={self.id} action={self.action} status={self.status}>"
