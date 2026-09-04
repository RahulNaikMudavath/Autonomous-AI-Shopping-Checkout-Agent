"""
AgentCart Phase 1: Architecture & Foundation Test Suite
Verifies:
1. System Health & Readiness Probes (/api/v1/health, /api/v1/ready)
2. Configuration Management (pydantic-settings)
3. Database Domain Models & Session Management (PostgreSQL/SQLAlchemy 2.0)
4. Redis Ephemeral State Store & Caching Layer
5. Shopping Sessions & Tasks API v1 CRUD Contracts
6. Standard RFC 7807 Error Envelopes & Correlation IDs
7. System Architecture Metadata API (/api/v1/system/info)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.core.config import get_settings, update_runtime_settings, AppSettings
from backend.core.errors import EntityNotFoundException, AgentCartException
from backend.database.models import (
    Base, User, UserPreference, ShoppingSession, ShoppingTask, AgentRun, AuditEvent
)
from backend.database.session import get_db_session, init_db, check_db_health
from backend.services.redis_service import get_redis_service, RedisService
from backend.services.session_service import SessionService
from backend.services.audit_service import AuditService

# =====================================================================
# Test Fixtures & In-Memory Test Database
# =====================================================================

TEST_SQLITE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db_session():
    """Provides an isolated test database session per test execution."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Initializes tables and dependencies before each test."""
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    # Flush Redis cache
    redis_service = get_redis_service()
    redis_service.flush()
    
    yield
    
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)


# =====================================================================
# 1. Health & Readiness Probe Tests
# =====================================================================

def test_api_health_liveness(client):
    """Verifies that /api/v1/health returns 200 OK with version and timestamp."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data
    assert "X-Request-ID" in response.headers


def test_root_health_alias(client):
    """Verifies root alias /health returns 200 OK for load balancers."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_api_readiness_probe(client):
    """Verifies /api/v1/ready checks database and Redis subsystems."""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["READY", "DEGRADED"]
    assert "database" in data
    assert "redis" in data
    assert data["database"]["healthy"] is True
    assert data["redis"]["healthy"] is True


def test_root_ready_alias(client):
    """Verifies root alias /ready returns 200 OK for Kubernetes probes."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "redis" in data


# =====================================================================
# 2. Configuration Management Tests
# =====================================================================

def test_configuration_loading_and_defaults():
    """Verifies AppSettings initializes with standard defaults."""
    settings = get_settings()
    assert settings.app_name == "AgentCart API"
    assert settings.api_v1_prefix == "/api/v1"
    assert isinstance(settings.cors_origins, list)
    assert settings.db_pool_size > 0


def test_runtime_configuration_update():
    """Verifies dynamic runtime configuration updates."""
    updated = update_runtime_settings({"environment": "test_env"})
    assert updated.environment == "test_env"
    
    # Restore
    update_runtime_settings({"environment": "development"})


# =====================================================================
# 3. Database Domain Models & CRUD Tests
# =====================================================================

def test_database_domain_models_creation():
    """Verifies User, UserPreference, ShoppingSession, and Task persistence."""
    db = TestingSessionLocal()
    try:
        # 1. Create User
        user = User(
            id="user_test_001",
            email="testuser@agentcart.io",
            name="Test User"
        )
        db.add(user)
        db.commit()

        # 2. Create User Preference
        pref = UserPreference(
            id="pref_001",
            user_id=user.id,
            brand_affinity=["Apple", "Sony"],
            price_sensitivity="premium",
            default_currency="INR"
        )
        db.add(pref)
        db.commit()

        # 3. Create Shopping Session
        session = ShoppingSession(
            id="session_test_001",
            user_id=user.id,
            title="Laptop Search Session",
            status="ACTIVE",
            session_metadata={"source": "test_suite"}
        )
        db.add(session)
        db.commit()

        # 4. Create Task
        task = ShoppingTask(
            id="task_test_001",
            session_id=session.id,
            raw_prompt="Find a high performance AI laptop under 150000 INR",
            status="PENDING"
        )
        db.add(task)
        db.commit()

        # 5. Query and Assert
        saved_user = db.query(User).filter(User.id == "user_test_001").first()
        assert saved_user is not None
        assert saved_user.email == "testuser@agentcart.io"
        assert saved_user.preferences is not None
        assert saved_user.preferences.brand_affinity == ["Apple", "Sony"]
        assert len(saved_user.sessions) == 1
        assert saved_user.sessions[0].title == "Laptop Search Session"
        assert len(saved_user.sessions[0].tasks) == 1

        # 6. Test Cascade Delete
        db.delete(saved_user)
        db.commit()
        assert db.query(ShoppingSession).filter(ShoppingSession.id == "session_test_001").first() is None
        assert db.query(ShoppingTask).filter(ShoppingTask.id == "task_test_001").first() is None

    finally:
        db.close()


def test_database_health_check_function():
    """Verifies check_db_health returns connected status and dialect."""
    res = check_db_health()
    assert res["status"] == "connected"
    assert res["healthy"] is True
    assert "latency_ms" in res


# =====================================================================
# 4. Redis Ephemeral State & Cache Tests
# =====================================================================

def test_redis_session_state_lifecycle():
    """Verifies storing, reading, and clearing temporary agent session state."""
    redis_service = get_redis_service()
    session_id = "sess_redis_123"
    state_payload = {
        "user_id": "usr_999",
        "current_intent": "search_laptops",
        "budget_limit": 120000
    }

    # Set state
    assert redis_service.set_session_state(session_id, state_payload, ttl_seconds=60) is True
    
    # Get state
    retrieved = redis_service.get_session_state(session_id)
    assert retrieved is not None
    assert retrieved["current_intent"] == "search_laptops"
    assert retrieved["budget_limit"] == 120000

    # Delete state
    assert redis_service.delete_session_state(session_id) is True
    assert redis_service.get_session_state(session_id) is None


def test_redis_general_caching():
    """Verifies key-value caching operations."""
    redis_service = get_redis_service()
    key = "cache:test_key"
    value = {"message": "hello_agentcart", "count": 42}

    assert redis_service.set(key, value, ttl=10) is True
    assert redis_service.exists(key) is True
    assert redis_service.get(key) == value
    assert redis_service.delete(key) is True
    assert redis_service.exists(key) is False


# =====================================================================
# 5. Shopping Sessions & Tasks API v1 Tests
# =====================================================================

def test_shopping_sessions_api_crud_lifecycle(client):
    """Verifies end-to-end REST lifecycle for shopping sessions and tasks."""
    # 1. Create Session
    create_payload = {
        "user_id": "usr_api_001",
        "title": "API Test Shopping Session",
        "session_metadata": {"platform": "web_test"}
    }
    create_res = client.post("/api/v1/shopping/sessions", json=create_payload)
    assert create_res.status_code == 201
    session_data = create_res.json()
    session_id = session_data["id"]
    assert session_data["title"] == "API Test Shopping Session"
    assert session_data["status"] == "ACTIVE"

    # 2. Get Session by ID
    get_res = client.get(f"/api/v1/shopping/sessions/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == session_id

    # 3. List Sessions
    list_res = client.get("/api/v1/shopping/sessions?user_id=usr_api_001")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert any(item["id"] == session_id for item in items)

    # 4. Add Task to Session
    task_payload = {
        "raw_prompt": "Looking for lightweight ultrabook with 32GB RAM",
        "extracted_constraints": {"ram_gb": 32, "weight": "light"}
    }
    task_res = client.post(f"/api/v1/shopping/sessions/{session_id}/tasks", json=task_payload)
    assert task_res.status_code == 201
    task_data = task_res.json()
    assert task_data["session_id"] == session_id
    assert task_data["raw_prompt"] == task_payload["raw_prompt"]

    # 5. List Tasks for Session
    tasks_list_res = client.get(f"/api/v1/shopping/sessions/{session_id}/tasks")
    assert tasks_list_res.status_code == 200
    tasks = tasks_list_res.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == task_data["id"]

    # 6. Update Session
    update_res = client.patch(
        f"/api/v1/shopping/sessions/{session_id}",
        json={"title": "Updated Title", "status": "COMPLETED"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Title"
    assert update_res.json()["status"] == "COMPLETED"

    # 7. Delete Session
    del_res = client.delete(f"/api/v1/shopping/sessions/{session_id}")
    assert del_res.status_code == 204

    # 8. Confirm Session Not Found
    get_after_del = client.get(f"/api/v1/shopping/sessions/{session_id}")
    assert get_after_del.status_code == 404


# =====================================================================
# 6. Error Handling & RFC 7807 Error Envelope Tests
# =====================================================================

def test_rfc7807_error_envelope_on_404(client):
    """Verifies that missing resources return the standardized RFC 7807 envelope."""
    response = client.get("/api/v1/shopping/sessions/non-existent-session-id")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    error = data["error"]
    assert error["code"] == "ENTITY_NOT_FOUND"
    assert "not found" in error["message"].lower()
    assert "timestamp" in error
    assert "request_id" in error
    assert "path" in error


def test_rfc7807_error_envelope_on_validation_error(client):
    """Verifies that invalid payloads return standard 422 error envelopes."""
    # Missing required 'user_id' field
    response = client.post("/api/v1/shopping/sessions", json={"title": "Missing user id"})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "REQUEST_VALIDATION_FAILED"
    assert "validation_errors" in data["error"]["details"]


# =====================================================================
# 7. Cryptographic Audit Trail Tests
# =====================================================================

def test_cryptographic_audit_ledger_chaining():
    """Verifies SHA-256 hash chaining and tamper verification."""
    db = TestingSessionLocal()
    try:
        # Record sequential events
        evt1 = AuditService.record_event(
            db, action="CREATE_SESSION", status="PASSED", session_id="s1", details={"step": 1}
        )
        assert evt1.prev_hash == "0" * 64
        assert len(evt1.sha256_hash) == 64

        evt2 = AuditService.record_event(
            db, action="POLICY_CHECK", status="PASSED", session_id="s1", details={"budget": 50000}
        )
        assert evt2.prev_hash == evt1.sha256_hash

        # Verify integrity
        integrity = AuditService.verify_ledger_integrity(db)
        assert integrity["valid"] is True
        assert integrity["total_events"] == 2

    finally:
        db.close()


# =====================================================================
# 8. System Architecture Metadata API Tests
# =====================================================================

def test_system_architecture_metadata_api(client):
    """Verifies /api/v1/system/info returns all 9 architecture layers with boundary rationales."""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "AgentCart API"
    assert "layers" in data
    assert len(data["layers"]) == 9
    
    # Verify key layer names
    layer_names = [l["name"] for l in data["layers"]]
    assert "Presentation & User Experience Layer" in layer_names
    assert "API Gateway & Security Layer" in layer_names
    assert "Agent Intelligence Layer" in layer_names
    assert "Trust, Safety & Policy Engine Layer" in layer_names
    assert "Universal Commerce & Merchant Abstraction Layer" in layer_names
    assert "Payment Abstraction & Delegated Auth Layer" in layer_names
    assert "Durable Data & Domain Storage Layer" in layer_names
    assert "Ephemeral State & Distributed Cache Layer" in layer_names
    assert "Observability, Telemetry & Evaluation Layer" in layer_names

    for layer in data["layers"]:
        assert len(layer["boundary_responsibility"]) > 10
        assert len(layer["isolation_rationale"]) > 10
