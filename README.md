# 🤖 AgentCart — Autonomous AI Shopping & Checkout Agent

> *"An AI agent that can autonomously discover, evaluate, purchase, and monitor products across multiple merchants while enforcing user-defined spending policies, authorization boundaries, and security constraints."*

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2019-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Bundler-Vite%208-646CFF.svg?style=flat&logo=vite)](https://vitejs.dev)
[![UCP](https://img.shields.io/badge/Commerce-UCP%20v1.0%20%2F%20MCP-indigo.svg)](https://modelcontextprotocol.io)
[![Tests](https://img.shields.io/badge/Tests-8%2F8%20Passing-brightgreen.svg)](#testing)

---

## 🧠 The 5 Architectural Layers

```
┌────────────────────────────────────────────────────────┐
│                   1. USER EXPERIENCE                   │
│  • Natural Language Shopping Assistant Chat            │
│  • Live Multi-Step Agent Execution Trace Timeline      │
│  • Dynamic Product Cards with Spec Badges & Price Tag  │
│  • Multi-Product Side-by-Side Comparison Matrix        │
│  • Human-in-the-Loop (HITL) Authorization Modal        │
│  • Spending Policy & Safety Control Center            │
│  • Real-Time Order Lifecycle & Return Console          │
└───────────────────────────┬────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────┐
│                 2. AGENT INTELLIGENCE                  │
│  • Intent & Requirement Extractor (Budget, Specs, Wts) │
│  • Multi-Merchant Autonomous Planner & Dispatcher      │
│  • Multi-Criteria Decision Analysis (MCDA) Engine      │
│  • Objective Value Scoring Formula & Performance Model │
│  • LLM Explainability & Recommendation Generator       │
│  • Autonomous Cart & Checkout Orchestration Action     │
└───────────────────────────┬────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────┐
│                 3. COMMERCE PROTOCOL                   │
│  • Universal Commerce Protocol (UCP v1.0) Endpoints    │
│  • Agent Commerce Protocol (ACP) Cart & Quotes         │
│  • Model Context Protocol (MCP) Tool Server            │
│  • Standardized Schemas for Discovery, Cart, Checkout  │
└───────────────────────────┬────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────┐
│              4. COMMERCE INFRASTRUCTURE                │
│  • 4 Participating Mock Merchants (TechHub,           │
│    ElectroBazaar, OmniStore, ProHardware Direct)       │
│  • Dynamic Pricing, Stock Inventory & Delivery Quotes  │
│  • Unified Multi-Merchant Cart Engine                  │
│  • Tokenized Mock Payment Gateway (UPI, Card, Escrow)  │
│  • Order Lifecycle State Machine & Return Engine       │
└───────────────────────────┬────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────┐
│                 5. TRUST & SAFETY                      │
│  • User Spending Policies (Ceiling, Item Cap, Velocity)│
│  • Human-in-the-Loop (HITL) Step-Up Thresholds         │
│  • Prompt Injection Defenses & Adversarial Sanitizer   │
│  • Price Gouging / Anomaly Detection                   │
│  • SHA-256 Chained Immutable Audit Trail               │
└────────────────────────────────────────────────────────┘
```

---

## 🛍️ The Core Scenario Walkthrough

### 1. User Prompt
> *"I need a laptop for AI/ML development under ₹1.2 lakh. 32GB RAM minimum. NVIDIA GPU. 1TB SSD. Prefer good battery life. Find the best value."*

### 2. Autonomous Agent Execution Trace
1. **Intent & Requirement Extraction**:
   - `Budget`: ≤ ₹120,000
   - `RAM`: ≥ 32 GB
   - `GPU`: NVIDIA (RTX 40-series preferred)
   - `Storage`: ≥ 1 TB
   - `Battery`: High priority (≥ 80Wh)
   - `Objective`: Best Value (MCDA Optimized)
2. **Multi-Merchant Discovery**:
   - Simultaneously queries 4 merchant catalog endpoints: *TechHub India*, *ElectroBazaar*, *OmniStore Online*, *ProHardware Direct*.
3. **MCDA Value Scoring & Spec Matching**:
   $$\text{MCDA Value Score} = w_{\text{perf}} \cdot \text{HardwareIndex} + w_{\text{price}} \cdot \text{HeadroomEfficiency} + w_{\text{battery}} \cdot \text{BatteryScore}$$

### 3. Product Comparison Matrix

| Product | Merchant | Price | GPU | RAM | SSD | Battery | Value Score | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Laptop A** (Helios Neo 16) | ElectroBazaar | ₹99,999 | RTX 4060 | 32GB | 1TB | 76Wh (6.5h) | **8.7** | Available |
| **Laptop B** (ROG Strix G16) | TechHub India | ₹109,999 | RTX 4070 | 32GB | 1TB | 90Wh (8.5h) | **9.4** | ⭐ **Top Pick** |
| **Laptop C** (Alienware ML Pro) | ProHardware | ₹117,999 | RTX 4070 | 64GB | 2TB | 86Wh (7.0h) | **9.1** | Available |

### 4. Agent Recommendation Explanation
> **Recommendation: Laptop B (ASUS ROG Strix G16 AI Workstation)**  
> *"It provides the best performance/value tradeoff (9.4/10) with its 140W RTX 4070 (+28% AI training TFLOPS over RTX 4060) and massive 90Wh battery while remaining ₹10,001 below your maximum ₹120,000 budget."*

---

## 🛡️ Trust & Safety System (Layer 5)

AgentCart implements strict enterprise guardrails to ensure agents do not exceed authorized boundaries:

1. **Spending Policy Ceiling**: Bar transactions exceeding maximum user budget (e.g. ₹150,000).
2. **Human-in-the-Loop (HITL) Authorization Threshold**: Purchases at or above the single-item limit (e.g. ₹50,000) trigger an authorization modal with tokenized PIN verification.
3. **Adversarial & Prompt Injection Defense**: Real-time heuristic and semantic regex defense engine intercepting system prompt overrides, fund transfer requests, and policy bypass attempts.
4. **Cryptographic SHA-256 Chained Audit Trail**: Every search, policy evaluation, cart change, checkout authorization, and order placement is appended as an immutable block whose hash depends on the previous block:
   $$\text{BlockHash}_n = \text{SHA256}(n \parallel \text{Timestamp} \parallel \text{Action} \parallel \text{Actor} \parallel \text{Payload} \parallel \text{BlockHash}_{n-1})$$

---

## ⚡ Universal Commerce Protocol (UCP v1.0) & MCP Tools

### Standard UCP Endpoints
- `GET /ucp/v1/merchants` — Discover registered UCP merchant nodes
- `POST /ucp/v1/catalog/search` — Unified catalog discovery
- `POST /ucp/v1/cart/quote` — Request tokenized pricing quote
- `POST /ucp/v1/checkout/execute` — Execute autonomous transaction
- `GET /ucp/v1/orders/{order_id}` — Real-time tracking
- `POST /ucp/v1/orders/{order_id}/returns` — Initiate autonomous return

### Model Context Protocol (MCP) Tools
- `search_products`
- `get_product_details`
- `calculate_value_score`
- `verify_spending_policy`
- `execute_checkout_order`
- `track_order_status`

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI backend server
python -m uvicorn backend.main:app --port 8000 --reload
```
API Documentation: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Testing

Run the comprehensive pytest suite covering all 5 architectural layers:
```bash
python -m pytest tests/ -v
```

Output:
```
tests/test_agent_and_safety.py::test_requirement_extraction_core_prompt PASSED
tests/test_agent_and_safety.py::test_mcda_value_scoring PASSED
tests/test_agent_and_safety.py::test_end_to_end_shopping_plan PASSED
tests/test_agent_and_safety.py::test_spending_policy_enforcement PASSED
tests/test_agent_and_safety.py::test_prompt_injection_detection PASSED
tests/test_agent_and_safety.py::test_cryptographic_audit_ledger_integrity PASSED
tests/test_agent_and_safety.py::test_cart_and_order_lifecycle PASSED
tests/test_agent_and_safety.py::test_mcp_tool_execution PASSED

============================== 8 passed in 0.24s ==============================
```

---

## 📜 License
MIT License. Built for autonomous AI commerce.
