# AgentCart: REST API Specification (v1)

This document defines the REST API conventions, endpoints, request/response payloads, and error schemas for AgentCart API v1.

All endpoints are prefixed with `/api/v1` unless noted otherwise.

---

## 1. Global Conventions

### Response Headers
Every response emitted by the API includes:
- `X-Request-ID`: Unique UUID tracking the request lifecycle across all subagents and logs.
- `X-Response-Time-MS`: Request execution time in milliseconds.

### Standard Error Envelope (RFC 7807 Inspired)
On any 4xx or 5xx status code, the response body follows this schema:

```json
{
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "ShoppingSession with ID 'sess_123' was not found.",
    "details": {
      "entity_name": "ShoppingSession",
      "entity_id": "sess_123"
    },
    "timestamp": "2026-09-04T09:20:00Z",
    "path": "/api/v1/shopping/sessions/sess_123",
    "request_id": "7b7a2d48-3606-4b68-9993-9c5950d99999"
  }
}
```

---

## 2. Health & Readiness Probes

### `GET /api/v1/health` (or `/health`)
**Summary**: Quick liveness probe.

**Response (200 OK)**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-09-04T09:20:00.123456+00:00"
}
```

---

### `GET /api/v1/ready` (or `/ready`)
**Summary**: Probes database and Redis dependencies.

**Response (200 OK or 503 Service Unavailable)**:
```json
{
  "status": "READY",
  "version": "1.0.0",
  "environment": "development",
  "database": {
    "status": "connected",
    "dialect": "postgresql",
    "latency_ms": 1.45,
    "healthy": true,
    "error": null
  },
  "redis": {
    "status": "connected",
    "mode": "redis_cluster_or_standalone",
    "latency_ms": 0.82,
    "healthy": true,
    "error": null
  },
  "timestamp": "2026-09-04T09:20:00.123456+00:00"
}
```

---

## 3. Shopping Sessions

### `POST /api/v1/shopping/sessions`
**Summary**: Creates a new shopping session for a user.

**Request Body**:
```json
{
  "user_id": "user_456",
  "title": "Search for Ultra HD 4K Monitor",
  "session_metadata": {
    "source": "web_ui",
    "client_version": "1.0.0"
  }
}
```

**Response (201 Created)**:
```json
{
  "id": "79b4a1b0-6421-4f11-9a99-4c2da2399999",
  "user_id": "user_456",
  "title": "Search for Ultra HD 4K Monitor",
  "status": "ACTIVE",
  "metadata": {
    "source": "web_ui",
    "client_version": "1.0.0"
  },
  "tasks_count": 0,
  "agent_runs_count": 0,
  "created_at": "2026-09-04T09:20:00.000000+00:00",
  "updated_at": "2026-09-04T09:20:00.000000+00:00"
}
```

---

### `GET /api/v1/shopping/sessions`
**Summary**: Lists shopping sessions with pagination and filters.

**Query Parameters**:
- `user_id` (optional, string): Filter by user ID.
- `status` (optional, string): Filter by status (`ACTIVE`, `COMPLETED`, `ABORTED`).
- `limit` (optional, integer, default: 20): Max items per page.
- `offset` (optional, integer, default: 0): Pagination offset.

**Response (200 OK)**:
```json
[
  {
    "id": "79b4a1b0-6421-4f11-9a99-4c2da2399999",
    "user_id": "user_456",
    "title": "Search for Ultra HD 4K Monitor",
    "status": "ACTIVE",
    "metadata": {},
    "tasks_count": 1,
    "agent_runs_count": 1,
    "created_at": "2026-09-04T09:20:00.000000+00:00",
    "updated_at": "2026-09-04T09:20:00.000000+00:00"
  }
]
```

---

### `GET /api/v1/shopping/sessions/{session_id}`
**Summary**: Retrieves a session by ID.

**Response (200 OK)**: Returns the `ShoppingSessionResponse` object.

---

### `PATCH /api/v1/shopping/sessions/{session_id}`
**Summary**: Updates session title, status, or metadata.

**Request Body**:
```json
{
  "title": "Completed Monitor Purchase",
  "status": "COMPLETED"
}
```

**Response (200 OK)**: Returns updated `ShoppingSessionResponse`.

---

### `DELETE /api/v1/shopping/sessions/{session_id}`
**Summary**: Permanently deletes a session and cascades deletes to all child tasks and runs.

**Response (204 No Content)**

---

## 4. Shopping Tasks Sub-Resource

### `POST /api/v1/shopping/sessions/{session_id}/tasks`
**Summary**: Attaches a new shopping prompt/goal to an active session.

**Request Body**:
```json
{
  "raw_prompt": "Find a gaming laptop with RTX 4070 and 32GB RAM under 150000 INR",
  "extracted_constraints": {
    "gpu": "RTX 4070",
    "ram_gb": 32,
    "max_price_inr": 150000
  },
  "execution_plan": [
    "extract_intent",
    "discover_merchant_catalogs",
    "rank_by_value",
    "evaluate_policy"
  ]
}
```

**Response (201 Created)**:
```json
{
  "id": "f8a7e443-85b7-4c31-b66a-119c8d599999",
  "session_id": "79b4a1b0-6421-4f11-9a99-4c2da2399999",
  "raw_prompt": "Find a gaming laptop with RTX 4070 and 32GB RAM under 150000 INR",
  "status": "PENDING",
  "extracted_constraints": {
    "gpu": "RTX 4070",
    "ram_gb": 32,
    "max_price_inr": 150000
  },
  "execution_plan": [
    "extract_intent",
    "discover_merchant_catalogs",
    "rank_by_value",
    "evaluate_policy"
  ],
  "created_at": "2026-09-04T09:20:00.000000+00:00",
  "updated_at": "2026-09-04T09:20:00.000000+00:00"
}
```

---

### `GET /api/v1/shopping/sessions/{session_id}/tasks`
**Summary**: Lists all tasks attached to the specified session.

**Response (200 OK)**: Returns a list of `ShoppingTaskResponse` objects.

---

## 5. System & Architecture Metadata

### `GET /api/v1/system/info`
**Summary**: Returns machine-readable descriptions of all 9 architectural layers, boundary responsibilities, and system health status.

**Response (200 OK)**:
```json
{
  "app_name": "AgentCart API",
  "version": "1.0.0",
  "environment": "development",
  "api_v1_prefix": "/api/v1",
  "layers": [
    {
      "layer_number": 1,
      "name": "Presentation & User Experience Layer",
      "boundary_responsibility": "Manages client interfaces, conversational input...",
      "isolation_rationale": "Decouples frontend rendering from backend business logic...",
      "status": "active"
    }
  ],
  "database_status": "connected",
  "redis_status": "connected",
  "timestamp": "2026-09-04T09:20:00.000000+00:00"
}
```
