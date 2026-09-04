# AgentCart: Environment Variables Reference

This document details all configuration options supported by AgentCart via `backend/core/config.py` and the `.env` file.

---

## 1. Core Application Settings

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | `str` | `"AgentCart API"` | Name of the application displayed in logs and system metadata. |
| `ENVIRONMENT` | `str` | `"development"` | Runtime environment (`development`, `staging`, `production`, `test`). |
| `DEBUG` | `bool` | `false` | Enables verbose debug logging and auto-reloading. |
| `API_V1_PREFIX` | `str` | `"/api/v1"` | URL prefix for version 1 REST routes. |
| `HOST` | `str` | `"0.0.0.0"` | Host interface to bind the uvicorn server. |
| `PORT` | `int` | `8000` | Port for the HTTP API server. |
| `CORS_ORIGINS` | `list[str]` | `["http://localhost:3000", ...]` | JSON list of allowed CORS origins. |

---

## 2. Database Settings (PostgreSQL)

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | `str` | `"postgresql://agentcart:securepass@localhost:5432/agentcart_db"` | PostgreSQL connection URI. Automatically falls back to SQLite if PostgreSQL is unreachable in local dev. |
| `DB_POOL_SIZE` | `int` | `10` | Number of persistent connections in the SQLAlchemy connection pool. |
| `DB_MAX_OVERFLOW` | `int` | `20` | Max overflow connections above pool size. |
| `DB_TIMEOUT_SECONDS` | `int` | `5` | Connection timeout in seconds. |

---

## 3. Redis Settings (Ephemeral State & Caching)

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `REDIS_URL` | `str` | `"redis://localhost:6379/0"` | Redis connection URL. Automatically falls back to in-memory store if unreachable. |
| `REDIS_TTL_SECONDS` | `int` | `3600` | Default time-to-live for ephemeral session state (1 hour). |
| `REDIS_TIMEOUT_SECONDS` | `int` | `2` | Connection timeout in seconds. |

---

## 4. LLM & AI Provider Settings (Reserved for Phase 2+)

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `OPENAI_API_KEY` | `str` | `""` | OpenAI API key for GPT models. |
| `GEMINI_API_KEY` | `str` | `""` | Google Gemini API key. |
| `ANTHROPIC_API_KEY` | `str` | `""` | Anthropic Claude API key. |
| `DEFAULT_LLM_PROVIDER` | `str` | `"local"` | Default LLM provider backend. |

---

## 5. Discovery & Search Settings (Reserved for Phase 3+)

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `SERPAPI_API_KEY` | `str` | `""` | SerpAPI key for live Google Shopping searches. |
| `TAVILY_API_KEY` | `str` | `""` | Tavily search API key. |
| `BRAVE_API_KEY` | `str` | `""` | Brave Search API key. |
| `LIVE_DISCOVERY_MODE` | `str` | `"auto"` | Product discovery mode (`auto`, `live`, `mock`). |

---

## 6. Payment & Wallet Sandbox (Reserved for Phase 5+)

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `STRIPE_SECRET_KEY` | `str` | `""` | Stripe test secret key. |
| `STRIPE_PUBLISHABLE_KEY` | `str` | `""` | Stripe test publishable key. |
| `RAZORPAY_KEY_ID` | `str` | `""` | Razorpay sandbox Key ID. |
| `RAZORPAY_KEY_SECRET` | `str` | `""` | Razorpay sandbox Secret. |

---

## 7. Observability & Telemetry

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `LANGFUSE_PUBLIC_KEY` | `str` | `""` | Langfuse public key for LLM tracing. |
| `LANGFUSE_SECRET_KEY` | `str` | `""` | Langfuse secret key. |
| `LANGFUSE_HOST` | `str` | `"https://cloud.langfuse.com"` | Langfuse cloud/self-hosted host. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `str` | `""` | OpenTelemetry OTLP collector gRPC/HTTP endpoint. |
