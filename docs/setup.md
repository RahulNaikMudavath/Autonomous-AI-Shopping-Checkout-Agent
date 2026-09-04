# AgentCart: Local & Docker Setup Guide

This guide outlines how to configure, run, and test AgentCart Phase 1 in local development and containerized Docker environments.

---

## 1. Prerequisites

- **Python**: Version 3.11 or higher
- **Node.js**: Version 18 or higher (Node 20 recommended) & npm
- **Docker & Docker Compose**: (Optional for local standalone mode, recommended for containerized testing)
- **Git**: For version control

---

## 2. Quickstart with Docker Compose (Recommended)

To start the entire multi-service stack (FastAPI Backend, React/Vite Frontend, PostgreSQL 16 with pgvector, Redis 7.2, and OpenTelemetry Collector):

```bash
# 1. Clone repository
git clone https://github.com/RahulNaikMudavath/Autonomous-AI-Shopping-Checkout-Agent.git
cd Autonomous-AI-Shopping-Checkout-Agent

# 2. Copy environment variables template
cp .env.example .env

# 3. Build and launch containers
docker compose up --build
```

### Service Endpoints
- **Frontend UI**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Liveness**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **API Readiness Probe**: [http://localhost:8000/api/v1/ready](http://localhost:8000/api/v1/ready)
- **System Architecture Info**: [http://localhost:8000/api/v1/system/info](http://localhost:8000/api/v1/system/info)
- **PostgreSQL**: `localhost:5432` (`user: agentcart`, `db: agentcart_db`)
- **Redis**: `localhost:6379`

---

## 3. Local Standalone Setup (Without Docker)

You can run AgentCart entirely on your local machine using Python virtual environments. If PostgreSQL or Redis are not running, the application automatically activates high-fidelity local SQLite and in-memory Redis fallbacks.

### Step 3.1: Backend Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment variables
cp .env.example .env

# 4. Start the FastAPI development server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3.2: Frontend Setup

```bash
# In a new terminal window:
cd frontend

# 1. Install Node dependencies
npm install

# 2. Start Vite development server
npm run dev
```

The frontend will be accessible at [http://localhost:3000](http://localhost:3000).

---

## 4. Database Migrations (Alembic)

To manage database schemas using Alembic:

```bash
# Run baseline migrations
alembic upgrade head

# Generate a new migration revision
alembic revision --autogenerate -m "add_new_columns"
```

---

## 5. Running Automated Tests

Run the complete test suite:

```bash
# Run all Phase 1 Foundation tests
pytest tests/test_phase1_foundation.py -v

# Run the complete test suite across all modules
pytest tests/ -v
```

---

## 6. Development Useful Commands

| Command | Purpose |
| :--- | :--- |
| `docker compose up -d` | Start containers in background |
| `docker compose down -v` | Stop containers and remove volumes |
| `docker compose logs -f backend` | Stream backend container logs |
| `pytest tests/ -v` | Run full test suite |
| `npm run build` (in frontend/) | Build production frontend bundle |
| `alembic upgrade head` | Apply database migrations |
