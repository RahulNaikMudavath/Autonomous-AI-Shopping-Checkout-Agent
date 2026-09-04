"""
Database Connection & Session Factory Module
Provides SQLAlchemy engine, session management, and connectivity health checks.
Supports SQLite fallback for lightweight local dev/testing if PostgreSQL is offline.
"""
import os
import time
import logging
from typing import Generator, Dict, Any
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from backend.core.config import get_settings
from backend.database.models import Base

logger = logging.getLogger("agentcart.database")

# Global singletons
_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Creates or returns the configured SQLAlchemy engine."""
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE

    settings = get_settings()
    db_url = settings.database_url
    
    # Try PostgreSQL connection first if configured
    if "postgresql" in db_url:
        try:
            logger.info("Attempting connection to PostgreSQL at %s", db_url.split("@")[-1] if "@" in db_url else db_url)
            engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_pre_ping=True,
                connect_args={"connect_timeout": settings.db_timeout_seconds}
            )
            # Verify connectivity with a quick query
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to PostgreSQL.")
            _ENGINE = engine
            return _ENGINE
        except Exception as e:
            logger.warning("PostgreSQL unreachable (%s). Initializing SQLite fallback for local runtime/tests.", str(e))
    
    # Fallback to local SQLite database
    sqlite_url = "sqlite:///./agentcart_local.db"
    _ENGINE = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    logger.info("Initialized local SQLite storage engine at agentcart_local.db")
    return _ENGINE


def init_db(engine: Engine | None = None) -> Engine:
    """Initializes the database schema by creating all registered domain tables."""
    global _ENGINE, _SESSION_FACTORY
    target_engine = engine or get_engine()
    
    _SESSION_FACTORY = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=target_engine
    )
    
    Base.metadata.create_all(bind=target_engine)
    logger.info("AgentCart database tables verified/created successfully.")
    return target_engine


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        init_db()
    
    session = _SESSION_FACTORY()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_health() -> Dict[str, Any]:
    """
    Performs a live query check against the database to assess responsiveness and dialect.
    """
    try:
        engine = get_engine()
        start = time.perf_counter()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        
        dialect_name = engine.dialect.name
        return {
            "status": "connected",
            "dialect": dialect_name,
            "latency_ms": round(latency_ms, 2),
            "healthy": True
        }
    except Exception as e:
        logger.error("Database health probe failed: %s", str(e))
        return {
            "status": "degraded",
            "dialect": "unknown",
            "error": str(e),
            "healthy": False
        }


def reset_db_engine():
    """Resets the singleton engine (useful in test suites to swap SQLite/PostgreSQL)."""
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is not None:
        _ENGINE.dispose()
    _ENGINE = None
    _SESSION_FACTORY = None
