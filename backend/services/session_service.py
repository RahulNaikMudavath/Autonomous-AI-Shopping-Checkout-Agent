"""
AgentCart Shopping Session Service
Encapsulates database operations and business logic for managing users,
shopping sessions, tasks, and agent run telemetry records.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from backend.database.models import User, UserPreference, ShoppingSession, ShoppingTask, AgentRun
from backend.domain.schemas import (
    ShoppingSessionCreate,
    ShoppingSessionUpdate,
    ShoppingTaskCreate
)
from backend.core.errors import EntityNotFoundException, ValidationException
from backend.services.redis_service import get_redis_service

logger = logging.getLogger("agentcart.services.session")


class SessionService:
    """Provides transactional domain operations for Shopping Sessions & Tasks."""

    @staticmethod
    def ensure_user(db: Session, user_id: str, email: Optional[str] = None, name: Optional[str] = None) -> User:
        """Retrieves an existing user or creates a default user profile."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user_email = email or f"{user_id}@agentcart.local"
            user_name = name or f"User {user_id}"
            user = User(
                id=user_id,
                email=user_email,
                name=user_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Created new user profile [id=%s, email=%s]", user.id, user.email)
        return user

    @staticmethod
    def create_session(db: Session, data: ShoppingSessionCreate) -> ShoppingSession:
        """Initializes a new shopping session in PostgreSQL and sets up Redis state."""
        # Ensure referenced user exists
        SessionService.ensure_user(db, data.user_id)

        session = ShoppingSession(
            user_id=data.user_id,
            title=data.title or "New Shopping Session",
            status="ACTIVE",
            session_metadata=data.session_metadata or {}
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Initialize temporary session state in Redis
        redis_service = get_redis_service()
        redis_service.set_session_state(
            session_id=session.id,
            state={
                "session_id": session.id,
                "user_id": session.user_id,
                "status": "ACTIVE",
                "current_step": "INITIALIZED",
                "active_tasks": []
            }
        )

        logger.info("Initialized shopping session [id=%s, user_id=%s]", session.id, session.user_id)
        return session

    @staticmethod
    def get_session(db: Session, session_id: str) -> ShoppingSession:
        """Fetches a session by ID or raises EntityNotFoundException."""
        session = db.query(ShoppingSession).filter(ShoppingSession.id == session_id).first()
        if not session:
            raise EntityNotFoundException(entity_name="ShoppingSession", entity_id=session_id)
        return session

    @staticmethod
    def list_sessions(
        db: Session,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ShoppingSession]:
        """Lists sessions with optional filtering and pagination."""
        query = db.query(ShoppingSession)
        if user_id:
            query = query.filter(ShoppingSession.user_id == user_id)
        if status:
            query = query.filter(ShoppingSession.status == status.upper())
        
        return query.order_by(desc(ShoppingSession.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def update_session(db: Session, session_id: str, data: ShoppingSessionUpdate) -> ShoppingSession:
        """Updates session attributes (title, status, metadata)."""
        session = SessionService.get_session(db, session_id)
        
        if data.title is not None:
            session.title = data.title
        if data.status is not None:
            session.status = data.status.upper()
        if data.session_metadata is not None:
            session.session_metadata = {**(session.session_metadata or {}), **data.session_metadata}
        
        db.commit()
        db.refresh(session)

        # Sync update with Redis
        redis_service = get_redis_service()
        current_state = redis_service.get_session_state(session_id) or {}
        current_state["status"] = session.status
        redis_service.set_session_state(session_id, current_state)

        logger.info("Updated shopping session [id=%s, status=%s]", session.id, session.status)
        return session

    @staticmethod
    def delete_session(db: Session, session_id: str) -> bool:
        """Deletes a shopping session and cascades deletes to tasks/runs."""
        session = SessionService.get_session(db, session_id)
        db.delete(session)
        db.commit()

        # Clean up Redis state
        redis_service = get_redis_service()
        redis_service.delete_session_state(session_id)

        logger.info("Deleted shopping session [id=%s]", session_id)
        return True

    @staticmethod
    def create_task(db: Session, session_id: str, data: ShoppingTaskCreate) -> ShoppingTask:
        """Adds a new discrete task or user goal to a shopping session."""
        # Verify session exists
        session = SessionService.get_session(db, session_id)
        
        task = ShoppingTask(
            session_id=session.id,
            raw_prompt=data.raw_prompt,
            status="PENDING",
            extracted_constraints=data.extracted_constraints or {},
            execution_plan=data.execution_plan or []
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Update Redis active tasks
        redis_service = get_redis_service()
        current_state = redis_service.get_session_state(session_id) or {}
        active_tasks = current_state.get("active_tasks", [])
        active_tasks.append({"task_id": task.id, "prompt": task.raw_prompt, "status": task.status})
        current_state["active_tasks"] = active_tasks
        redis_service.set_session_state(session_id, current_state)

        logger.info("Added shopping task [id=%s, session_id=%s]", task.id, session_id)
        return task

    @staticmethod
    def get_tasks_for_session(db: Session, session_id: str) -> List[ShoppingTask]:
        """Retrieves all tasks associated with a session."""
        # Verify session exists
        SessionService.get_session(db, session_id)
        return db.query(ShoppingTask).filter(ShoppingTask.session_id == session_id).order_by(ShoppingTask.created_at).all()

    @staticmethod
    def record_agent_run(
        db: Session,
        session_id: str,
        supervisor_agent: str = "LangGraphSupervisor",
        status: str = "COMPLETED",
        latency_ms: int = 0,
        tokens: int = 0,
        cost_usd: float = 0.0,
        trace_steps: Optional[List] = None
    ) -> AgentRun:
        """Records an agent run execution trace and cost telemetry."""
        # Verify session exists
        SessionService.get_session(db, session_id)
        
        run = AgentRun(
            session_id=session_id,
            supervisor_agent=supervisor_agent,
            status=status,
            total_latency_ms=latency_ms,
            total_tokens=tokens,
            estimated_cost_usd=cost_usd,
            trace_steps=trace_steps or []
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        logger.info("Recorded agent run telemetry [id=%s, session_id=%s, latency=%dms]", run.id, session_id, latency_ms)
        return run
