"""
AgentCart Shopping Sessions & Tasks API Endpoints (v1)
Handles session lifecycle, goal attachment, and task queries according to Phase 1 contracts.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db_session
from backend.services.session_service import SessionService
from backend.domain.schemas import (
    ShoppingSessionCreate,
    ShoppingSessionUpdate,
    ShoppingSessionResponse,
    ShoppingTaskCreate,
    ShoppingTaskResponse
)

logger = logging.getLogger("agentcart.api.sessions")

sessions_router = APIRouter(prefix="/shopping/sessions", tags=["Shopping Sessions"])


@sessions_router.post(
    "",
    response_model=ShoppingSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Shopping Session",
    description="Initializes a new shopping session for a given user."
)
async def create_shopping_session(
    payload: ShoppingSessionCreate,
    db: Session = Depends(get_db_session)
):
    session = SessionService.create_session(db, payload)
    return ShoppingSessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        status=session.status,
        metadata=session.session_metadata or {},
        tasks_count=0,
        agent_runs_count=0,
        created_at=session.created_at.isoformat() if session.created_at else None,
        updated_at=session.updated_at.isoformat() if session.updated_at else None
    )


@sessions_router.get(
    "",
    response_model=List[ShoppingSessionResponse],
    summary="List Shopping Sessions",
    description="Retrieves a paginated list of shopping sessions with optional user or status filters."
)
async def list_shopping_sessions(
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
    status: Optional[str] = Query(default=None, description="Filter by status (ACTIVE, COMPLETED, ABORTED)"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db_session)
):
    sessions = SessionService.list_sessions(db, user_id=user_id, status=status, limit=limit, offset=offset)
    results = []
    for s in sessions:
        results.append(
            ShoppingSessionResponse(
                id=s.id,
                user_id=s.user_id,
                title=s.title,
                status=s.status,
                metadata=s.session_metadata or {},
                tasks_count=len(s.tasks) if s.tasks else 0,
                agent_runs_count=len(s.agent_runs) if s.agent_runs else 0,
                created_at=s.created_at.isoformat() if s.created_at else None,
                updated_at=s.updated_at.isoformat() if s.updated_at else None
            )
        )
    return results


@sessions_router.get(
    "/{session_id}",
    response_model=ShoppingSessionResponse,
    summary="Get Shopping Session",
    description="Retrieves details of a specific shopping session by ID."
)
async def get_shopping_session(
    session_id: str,
    db: Session = Depends(get_db_session)
):
    session = SessionService.get_session(db, session_id)
    return ShoppingSessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        status=session.status,
        metadata=session.session_metadata or {},
        tasks_count=len(session.tasks) if session.tasks else 0,
        agent_runs_count=len(session.agent_runs) if session.agent_runs else 0,
        created_at=session.created_at.isoformat() if session.created_at else None,
        updated_at=session.updated_at.isoformat() if session.updated_at else None
    )


@sessions_router.patch(
    "/{session_id}",
    response_model=ShoppingSessionResponse,
    summary="Update Shopping Session",
    description="Updates session title, status, or metadata."
)
async def update_shopping_session(
    session_id: str,
    payload: ShoppingSessionUpdate,
    db: Session = Depends(get_db_session)
):
    session = SessionService.update_session(db, session_id, payload)
    return ShoppingSessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        status=session.status,
        metadata=session.session_metadata or {},
        tasks_count=len(session.tasks) if session.tasks else 0,
        agent_runs_count=len(session.agent_runs) if session.agent_runs else 0,
        created_at=session.created_at.isoformat() if session.created_at else None,
        updated_at=session.updated_at.isoformat() if session.updated_at else None
    )


@sessions_router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Shopping Session",
    description="Permanently deletes a shopping session and cascades deletes to all child tasks."
)
async def delete_shopping_session(
    session_id: str,
    db: Session = Depends(get_db_session)
):
    SessionService.delete_session(db, session_id)
    return None


# =====================================================================
# Tasks Sub-Resource Endpoints
# =====================================================================

@sessions_router.post(
    "/{session_id}/tasks",
    response_model=ShoppingTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Task to Session",
    description="Attaches a new shopping prompt/task to an active session."
)
async def create_shopping_task(
    session_id: str,
    payload: ShoppingTaskCreate,
    db: Session = Depends(get_db_session)
):
    task = SessionService.create_task(db, session_id, payload)
    return ShoppingTaskResponse(
        id=task.id,
        session_id=task.session_id,
        raw_prompt=task.raw_prompt,
        status=task.status,
        extracted_constraints=task.extracted_constraints or {},
        execution_plan=task.execution_plan or [],
        created_at=task.created_at.isoformat() if task.created_at else None,
        updated_at=task.updated_at.isoformat() if task.updated_at else None
    )


@sessions_router.get(
    "/{session_id}/tasks",
    response_model=List[ShoppingTaskResponse],
    summary="List Tasks in Session",
    description="Lists all tasks recorded under a specific shopping session."
)
async def list_shopping_tasks(
    session_id: str,
    db: Session = Depends(get_db_session)
):
    tasks = SessionService.get_tasks_for_session(db, session_id)
    results = []
    for t in tasks:
        results.append(
            ShoppingTaskResponse(
                id=t.id,
                session_id=t.session_id,
                raw_prompt=t.raw_prompt,
                status=t.status,
                extracted_constraints=t.extracted_constraints or {},
                execution_plan=t.execution_plan or [],
                created_at=t.created_at.isoformat() if t.created_at else None,
                updated_at=t.updated_at.isoformat() if t.updated_at else None
            )
        )
    return results
