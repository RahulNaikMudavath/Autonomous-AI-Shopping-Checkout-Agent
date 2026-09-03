# 🤖 AgentCart — Autonomous AI Shopping & Checkout Agent

> *"An AI agent that can autonomously discover, evaluate, purchase, and monitor products across multiple merchants while enforcing user-defined spending policies, authorization boundaries, and security constraints."*

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2019-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Bundler-Vite%208-646CFF.svg?style=flat&logo=vite)](https://vitejs.dev)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![pgvector](https://img.shields.io/badge/Vector%20DB-pgvector-cyan.svg)](https://github.com/pgvector/pgvector)
[![OpenTelemetry](https://img.shields.io/badge/Observability-OpenTelemetry-rose.svg)](https://opentelemetry.io)
[![Langfuse](https://img.shields.io/badge/LLM%20Tracing-Langfuse-indigo.svg)](https://langfuse.com)
[![Docker](https://img.shields.io/badge/Container-Docker%20Compose-blue.svg)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-59%2F59%20Passing-brightgreen.svg)](#testing)

---

## 🏗️ 13. System Architecture & Topology

```
                         USER
                          │
                          ▼
                 ┌─────────────────┐
                 │   Next.js UI    │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │    FastAPI      │
                 │  API Gateway    │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Agent Supervisor│
                 │   LangGraph     │
                 └────────┬────────┘
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
      Intent          Discovery          Policy
       Agent            Agent            Engine
          │               │                │
          │               ▼                │
          │          ┌─────────┐           │
          │          │Merchant │           │
          │          │ Gateway │           │
          │          └────┬────┘           │
          │               │                │
          │       ┌───────┼───────┐        │
          │       ▼       ▼       ▼        │
          │      M-A     M-B     M-C       │
          │                                │
          └──────────────┬─────────────────┘
                         ▼
                  Ranking Agent
                         │
                         ▼
                    Cart Agent
                         │
                         ▼
                  Checkout Agent
                         │
                         ▼
                 Authorization Layer
                         │
                   ┌─────┴─────┐
                   │           │
              Auto Approve   Human
                   │         Approval
                   │           │
                   └─────┬─────┘
                         ▼
                   Payment Agent
                         │
                         ▼
                  Payment Sandbox
                         │
                         ▼
                    Merchant
                         │
                         ▼
                    Order Agent
                         │
                         ▼
                 Order Tracking
```

### Supporting Infrastructure
- **PostgreSQL 16**: Relational storage for orders, user profiles, policy rules, and cryptographic audit blocks.
- **Redis 7.2**: Ephemeral session working memory, token bucket rate limits, and cart mutex locks.
- **pgvector**: Cosine similarity vector index for unstructured natural language user preference retrieval.
- **OpenTelemetry Collector**: W3C distributed trace context propagation and subagent latency flamegraphs.
- **Langfuse**: LLM prompt lineage tracking, token accounting, and cost monitoring ($0.038 / workflow).
- **Docker & Docker Compose**: Production containerization (`Dockerfile`, `docker-compose.yml`).
- **GitHub Actions**: Automated CI/CD matrix executing 59+ pytest unit tests on push.

---

## 🌟 The 13 Core Architectural Milestones

### 1. 🎯 The North Star Vision & 5 Layers
Multi-agent commerce stack separating **User Experience (Layer 1)**, **Agent Intelligence (Layer 2)**, **Commerce Protocol (Layer 3)**, **Commerce Infrastructure (Layer 4)**, and **Trust & Safety (Layer 5)**.

### 2. 🤖 The Agent Brain
Hierarchical orchestrator featuring **Intent Extractor**, **Task Planner**, **Context Store**, and **Supervisor State Machine**.

### 3. 🧩 Specialized Agents
- **Intent Agent**: Converts unstructured queries into exact typed JSON constraints (`category`, `budget`, `ram_gb`, `storage_gb`, `gpu`, `optimization`).
- **Planning Agent**: Generates deterministic multi-step DAGs.
- **Discovery Agent**: Parallel discovery across federated merchants.

### 4. 🏪 Merchant Simulator
4 standalone merchant systems (`merchant-a` to `merchant-d`) exposing 8 standard REST endpoints:
`GET /products`, `GET /products/{id}`, `POST /cart`, `PATCH /cart/{id}`, `POST /checkout`, `POST /payment`, `GET /orders/{id}`, `POST /returns`.

### 5. 🔌 Protocol Layer
Unified Commerce Gateway exposing 8 standardized commerce capabilities (`discover_products`, `get_product`, `create_cart`, `update_cart`, `checkout`, `authorize_payment`, `get_order`, `cancel_order`) via REST, MCP Tools, and UCP-compatible envelopes.

### 6. 💳 Payment Architecture (Zero Raw Cards & Delegated Authorization)
- **Zero raw card storage**: Only single-use scoped authorization tokens (`AUTH_MANDATE_...`).
- **Bounded autonomy category rules**:
  - Groceries $\le ₹3,000 \rightarrow$ **AUTO APPROVE**
  - Electronics $\le ₹10,000 \rightarrow$ **AUTO APPROVE**
  - Electronics $> ₹10,000 \rightarrow$ **ASK USER (PIN/Biometric)**
  - Single transaction $> ₹25,000 \rightarrow$ **BLOCK**

### 7. 🛡️ Agent Security (Prompt Injection Defense)
Multi-stage sanitizer defusing adversarial prompts:
```
Merchant content ➔ Untrusted context ➔ Sanitizer ➔ Policy boundary ➔ LLM
```
```
⚠ Untrusted instruction detected.
Ignoring merchant instruction.
Continuing according to user policy.
```

### 8. 🔐 Tool Permissions (Agent RBAC Matrix)
```
                 Tool Permission Matrix

                 Search Cart Checkout Payment
------------------------------------------------
Discovery Agent    ✓     ✗       ✗       ✗
Ranking Agent      ✓     ✗       ✗       ✗
Cart Agent         ✓     ✓       ✗       ✗
Checkout Agent     ✓     ✓       ✓       ✗
Payment Agent      ✗     ✗       ✓       ✓
Order Agent        ✗     ✗       ✗       ✗
```

### 9. 🔄 Distributed Failure Recovery (6 Scenarios)
1. **Price Change**: $₹99,999 \rightarrow ₹104,999 \rightarrow$ Autonomous search replanning and candidate re-ranking.
2. **Inventory Disappearance**: Stock drops to $0 \rightarrow$ Multi-merchant SKU substitution.
3. **Payment Decline**: Bank declines UPI $\rightarrow$ Automatic failover to Virtual Visa Token.
4. **Merchant API Timeout**: 504 Gateway Error $\rightarrow$ Exponential backoff retry (200ms, 400ms, 800ms).
5. **Agent Tool Crash**: ContextStore snapshot rollback and checkpoint restoration.
6. **Lost Webhook**: Dropped async notification $\rightarrow$ Active order polling reconciliation.

### 10. 🧠 Multi-Tier Memory Subsystem
- **Tier 1 (User Profile)**: Preferred brands, category budgets, form factors, shipping address.
- **Tier 2 (Transaction Memory)**: Lifetime orders, receipts, spend logs, RMA returns.
- **Tier 3 (Working Memory)**: Active session DAG state, scratchpad, cart lock.
- **Tier 4 (Semantic Vector DB)**: pgvector / Cosine similarity retrieval for natural language directives (*"I prefer lightweight laptops"*, *"I usually buy Logitech peripherals"*, *"Don't recommend refurbished products"*).

### 11. 📈 Agent Observability
- **Execution Waterfall Trace**:
  ```
  12:31:02  Intent Agent     ✓ Requirements extracted
  12:31:03  Planner          ✓ Created shopping plan
  12:31:03  Merchant A       ✓ 17 products
  12:31:04  Merchant B       ✓ 23 products
  12:31:05  Ranking Agent    ✓ Top 5 selected
  12:31:06  Policy Engine    ✓ Purchase permitted
  12:31:07  Cart Agent       ✓ Cart created
  12:31:08  Checkout Agent   ✓ Final total calculated
  12:31:08  Authorization    ⚠ User approval required
  ```
- **Operational Metrics**: Steps (11), Tool Calls (17), Latency (2.8s), Tokens (4,823), Cost ($0.04), Retries (1), Violations (0).

### 12. 🧪 Automated Benchmark Evaluation (TC01 - TC12)
```
┌───────────────────────────────────────────────┐
│        BENCHMARK EVALUATION METRICS           │
├───────────────────────────────────────────────┤
│ Total Simulated Workflows        120 runs     │
│ Task Success Rate                98.3%        │
│ Constraint Satisfaction Rate     100.0%       │
│ Unauthorized Action Rate         0.0%         │
│ Tool-Call Accuracy               99.4%        │
│ Recovery Success Rate            96.8%        │
│ Average Latency                  2.1 s        │
│ Average Token Cost               $0.038       │
└───────────────────────────────────────────────┘
```

### 13. 🔮 Protocol-Aware Roadmap (Shopify UCP, MCP & Native Agent Protocols)

```
                    AgentCart
                       │
              ┌────────┴────────┐
              │ Commerce Gateway│
              └────────┬────────┘
                       │
            ┌──────────┼──────────┐
            ↓          ↓          ↓
          REST        MCP      UCP-style
          APIs       Server    capability
            │          │          │
            └──────────┼──────────┘
                       ↓
                   Merchants
```

- **Protocol-Aware Integration**: Evolving from protocol-inspired simulation to native binding with **Shopify's UCP-oriented commerce tools** (catalog discovery, cart creation, dynamic checkout, and order monitoring).
- **Model Context Protocol (MCP)**: Exposing standard tools (`search_products`, `create_cart`, `execute_checkout`) as reusable MCP server endpoints for third-party LLMs (Claude, GPT-4, Gemini).
- **Delegated Authorization & Bounded Autonomy**: Pioneering policy-first delegated payments with India's emerging framework for rule-based autonomous agent transactions.

---

## 🚀 Quickstart Guide

### 1. Run Locally

```bash
# Clone the repository
git clone https://github.com/RahulNaikMudavath/Autonomous-AI-Shopping-Checkout-Agent.git
cd "Autonomous AI Shopping & Checkout Agent"

# Setup & start backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Setup & start frontend (in another terminal)
cd frontend
npm install
npm run dev
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

---

## 🧪 Testing Suite (59/59 Passing)

```bash
python -m pytest tests/ -v
```

```
tests/test_agent_and_safety.py (8 tests) ................... PASSED
tests/test_agent_brain_multiagent.py (8 tests) ............. PASSED
tests/test_specialized_agents.py (3 tests) ................. PASSED
tests/test_merchant_simulator.py (2 tests) ................. PASSED
tests/test_commerce_gateway.py (2 tests) ................... PASSED
tests/test_payment_architecture_delegated_auth.py (7 tests)  PASSED
tests/test_agent_security_sanitizer.py (4 tests) ........... PASSED
tests/test_agent_tool_permissions.py (6 tests) ............. PASSED
tests/test_failure_recovery_engine.py (6 tests) ............ PASSED
tests/test_memory_system.py (6 tests) ...................... PASSED
tests/test_agent_observability.py (3 tests) ................ PASSED
tests/test_evaluation_framework.py (2 tests) ............... PASSED
tests/test_system_architecture_and_infrastructure.py (2 tests) PASSED

============================= 59 passed in 1.10s ==============================
```

---

## 📜 License
MIT License. Built for Autonomous Commerce & Agentic AI Research.
