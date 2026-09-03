"""
AgentCart Main Application
FastAPI Server connecting all 5 layers:
- User Experience APIs
- Agent Intelligence: Hierarchical Multi-Agent Supervisor & Context Store
- Specialized Agents: Agent 1 (Intent), Agent 2 (Planner), Agent 3 (Discovery)
- Merchant Commerce REST APIs: Merchant A, B, C, D
- Universal Commerce Protocol (UCP v1.0) & MCP Tools
- Commerce Infrastructure (Merchants, Cart, Order Engine)
- Trust & Safety Guardrails & Cryptographic Audit Ledger
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.schemas import (
    UserRequirements, RecommendationResult, Product, Cart, Order, SpendingPolicy,
    PolicyCheckResult, PromptInjectionScanResult, AuditBlock, MCPToolCallRequest, MCPToolCallResponse
)
from backend.agent.intent_agent import IntentAgent, StructuredIntentState
from backend.agent.planning_agent import PlanningAgent, PlanningExecutionResult
from backend.agent.supervisor import AgentSupervisor
from backend.agent.context_store import ContextStore
from backend.agent.subagents.discovery_agent import DiscoveryAgent
from backend.agent.subagents.ranking_agent import RankingAgent
from backend.agent.checkout_pipeline import CheckoutPipeline
from backend.infrastructure.merchants import get_all_merchants, search_merchant_catalog
from backend.infrastructure.merchant_apis import merchant_apis_router
from backend.infrastructure.cart_order_engine import (
    get_or_create_cart, add_to_cart, remove_from_cart, clear_cart,
    get_all_orders, get_order_by_id, process_return_request
)
from backend.trust_safety.policy_engine import (
    get_current_policy, update_policy, evaluate_spending_policy,
    scan_for_prompt_injection, get_audit_ledger, verify_audit_ledger_integrity, add_audit_log
)
from backend.protocol.ucp import ucp_router
from backend.protocol.mcp_server import MCP_TOOLS_SPEC, handle_mcp_tool_call

from backend.protocol.gateway_router import gateway_router
from backend.infrastructure.merchant_simulator import merchant_sim_router

app = FastAPI(
    title="AgentCart - Autonomous AI Shopping & Checkout Agent",
    description="5-Layer Autonomous Commerce Intelligence System with Specialized Agents & Dedicated Merchant APIs",
    version="1.4.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(ucp_router)
app.include_router(gateway_router)
app.include_router(merchant_apis_router)
app.include_router(merchant_sim_router)

# Request payloads
class ChatQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "session_default"

class IntentParseRequest(BaseModel):
    query: str

class PlannerExecuteRequest(BaseModel):
    query: str
    cart_id: Optional[str] = "default_user_cart"

class AddToCartRequest(BaseModel):
    cart_id: Optional[str] = "default_user_cart"
    product_id: str
    quantity: int = 1

class CheckoutDirectRequest(BaseModel):
    product_id: str
    shipping_address: Optional[str] = "Rahul N., Flat 402, HighTech Tech Park, Bangalore 560100"
    payment_method: Optional[str] = "UPI (Tokenized 1-Click)"
    user_confirmed: bool = True
    session_id: Optional[str] = "session_default"

class TestInjectionRequest(BaseModel):
    prompt_text: str

# -------------------------------------------------------------
# 1. Specialized Agents (Intent Agent, Planning Agent) Endpoints
# -------------------------------------------------------------

@app.post("/api/agents/intent/parse", response_model=StructuredIntentState)
async def parse_intent_to_state(req: IntentParseRequest):
    """
    Agent 1 — Intent Agent endpoint.
    Converts 'I need a laptop for coding and AI under 1.2L' into exact structured state.
    """
    return IntentAgent.parse_query_to_state(req.query)

@app.post("/api/agents/planner/execute-dag", response_model=PlanningExecutionResult)
async def execute_planning_dag(req: PlannerExecuteRequest):
    """
    Agent 2 — Planning Agent endpoint.
    Executes the 8-step commerce DAG sequentially with status updates.
    """
    intent_state = IntentAgent.parse_query_to_state(req.query)
    
    # Discovery wrapper
    reqs_adapter = UserRequirements(
        raw_query=req.query,
        budget_max_inr=intent_state.budget.max,
        min_ram_gb=intent_state.requirements.ram_gb.min if intent_state.requirements.ram_gb else 16,
        min_ssd_gb=intent_state.requirements.storage_gb.min if intent_state.requirements.storage_gb else 512,
        gpu_brand_preference=intent_state.requirements.gpu or "NVIDIA",
        objective="best_value"
    )

    def run_discovery():
        return DiscoveryAgent.discover_candidates(reqs_adapter)

    def run_ranking(candidates):
        return RankingAgent.rank_and_evaluate(candidates, reqs_adapter)

    return PlanningAgent.execute_plan(
        intent_state=intent_state,
        discovery_fn=run_discovery,
        ranking_fn=run_ranking,
        cart_id=req.cart_id or "default_user_cart"
    )

# -------------------------------------------------------------
# 2. Shopping Assistant & Agent Brain Endpoints
# -------------------------------------------------------------

@app.post("/api/chat", response_model=RecommendationResult)
async def process_shopping_query(req: ChatQueryRequest):
    """
    Main shopping assistant endpoint. Runs hierarchical multi-agent reasoning:
    User -> Intent Extractor -> Task Planner -> Context Store & Policy Engine -> Agent Supervisor -> [Discovery, Ranking, Merchant Agents] -> Recommendation.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    return AgentSupervisor.process_request(query=req.query, session_id=req.session_id or "session_default")

@app.get("/api/agent-brain/state")
async def get_agent_brain_state(session_id: str = "session_default"):
    """Returns active session context, working memory, and current execution stage."""
    session = ContextStore.get_or_create_session(session_id)
    profile = ContextStore.get_user_profile()
    return {
        "session": session.model_dump(),
        "user_profile": profile.model_dump(),
        "active_subagents": ["DiscoveryAgent", "RankingAgent", "MerchantAgent"],
        "supervisor_status": "ONLINE"
    }

@app.get("/api/products", response_model=List[Product])
async def get_catalog(category: Optional[str] = None, max_price: Optional[float] = None):
    """Retrieve all products from the multi-merchant catalog."""
    return search_merchant_catalog(category=category, max_price=max_price)

# -------------------------------------------------------------
# 3. Cart & Commerce Infrastructure Endpoints
# -------------------------------------------------------------

@app.get("/api/cart", response_model=Cart)
async def get_user_cart(cart_id: str = "default_user_cart"):
    """Retrieve current state of user shopping cart."""
    return get_or_create_cart(cart_id)

@app.post("/api/cart/add", response_model=Cart)
async def add_item_to_cart(req: AddToCartRequest):
    """Add product to stateful multi-merchant cart."""
    products = search_merchant_catalog()
    product = next((p for p in products if p.id == req.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    cart = add_to_cart(req.cart_id or "default_user_cart", product, req.quantity)
    add_audit_log(
        action_type="CART_ADD",
        actor="USER",
        payload_summary=f"Added '{product.title}' (Qty: {req.quantity}) to cart.",
        policy_verified=True
    )
    return cart

@app.delete("/api/cart/item/{product_id}", response_model=Cart)
async def remove_item_from_cart(product_id: str, cart_id: str = "default_user_cart"):
    """Remove product from shopping cart."""
    return remove_from_cart(cart_id, product_id)

@app.delete("/api/cart", response_model=Cart)
async def empty_cart(cart_id: str = "default_user_cart"):
    """Clear all items in shopping cart."""
    return clear_cart(cart_id)

@app.post("/api/checkout/authorize-and-pay", response_model=Order)
async def direct_checkout(req: CheckoutDirectRequest):
    """
    Executes stage-gated checkout: Cart -> Checkout -> Authorization -> Payment -> Order.
    """
    products = search_merchant_catalog()
    product = next((p for p in products if p.id == req.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    try:
        order, traces = CheckoutPipeline.execute_stage_gated_checkout(
            product=product,
            session_id=req.session_id or "session_default",
            user_confirmed=req.user_confirmed,
            shipping_address=req.shipping_address,
            payment_method=req.payment_method or "UPI (Tokenized 1-Click)"
        )
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------
# 4. Order Lifecycle & Return Management Endpoints
# -------------------------------------------------------------

@app.get("/api/orders", response_model=List[Order])
async def list_orders():
    """List all placed orders and current tracking states."""
    return get_all_orders()

@app.get("/api/orders/{order_id}", response_model=Order)
async def get_order_details(order_id: str):
    """Retrieve detailed order tracking and receipt."""
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.post("/api/orders/{order_id}/return", response_model=Order)
async def request_order_return(order_id: str, payload: Dict[str, str]):
    """Initiate an autonomous return and refund workflow."""
    reason = payload.get("reason", "Customer requested return")
    order = process_return_request(order_id, reason)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    add_audit_log(
        action_type="RETURN_REQUESTED",
        actor="USER",
        payload_summary=f"Return requested for Order {order_id}. Reason: {reason}",
        policy_verified=True
    )
    return order

# -------------------------------------------------------------
# 5. Trust & Safety, Policies & Cryptographic Ledger Endpoints
# -------------------------------------------------------------

@app.get("/api/policy", response_model=SpendingPolicy)
async def get_policy_settings():
    """Retrieve active user spending policies and authorization boundaries."""
    return get_current_policy()

@app.put("/api/policy", response_model=SpendingPolicy)
async def update_policy_settings(policy: SpendingPolicy):
    """Update user spending policies and authorization boundaries."""
    return update_policy(policy)

@app.post("/api/policy/test-injection", response_model=PromptInjectionScanResult)
async def test_prompt_injection_detection(req: TestInjectionRequest):
    """Sandbox endpoint to test adversarial prompt injection detection."""
    return scan_for_prompt_injection(req.prompt_text)

@app.get("/api/audit-ledger", response_model=List[AuditBlock])
async def view_cryptographic_audit_ledger():
    """Retrieve immutable append-only SHA-256 chained transaction audit ledger."""
    return get_audit_ledger()

@app.get("/api/audit-ledger/verify")
async def verify_ledger():
    """Cryptographically verifies hash continuity across all blocks in the ledger."""
    return verify_audit_ledger_integrity()

# -------------------------------------------------------------
# 6. MCP (Model Context Protocol) Server Tool Endpoints
# -------------------------------------------------------------

@app.get("/api/mcp/tools")
async def get_mcp_tool_definitions():
    """List all available MCP tools supported by AgentCart."""
    return {"tools": MCP_TOOLS_SPEC}

@app.post("/api/mcp/call", response_model=MCPToolCallResponse)
async def execute_mcp_tool(req: MCPToolCallRequest):
    """Directly execute an MCP tool."""
    return handle_mcp_tool_call(req)

# -------------------------------------------------------------
# 7. Payment Architecture & Delegated Authorization Endpoints
# -------------------------------------------------------------
from backend.infrastructure.payment_wallet_sandbox import (
    PaymentWalletSandbox, TokenizedPaymentMethod, SandboxChargeRequest, SandboxChargeResponse
)
from backend.trust_safety.delegated_auth_policy import (
    DelegatedAuthPolicyEngine, DelegatedAuthEvaluationRequest, DelegatedAuthDecision, DelegatedPolicySettings
)

@app.get("/api/payment/wallet", response_model=List[TokenizedPaymentMethod])
async def get_user_payment_wallet():
    """Retrieve tokenized payment wallet instruments (Zero raw card numbers stored)."""
    return PaymentWalletSandbox.get_wallet_instruments()

@app.get("/api/payment/policy", response_model=DelegatedPolicySettings)
async def get_delegated_policy():
    """Retrieve category bounded autonomy rules and hard transaction ceilings."""
    return DelegatedAuthPolicyEngine.get_policy()

@app.post("/api/payment/evaluate-delegated-auth", response_model=DelegatedAuthDecision)
async def evaluate_delegated_authorization(req: DelegatedAuthEvaluationRequest):
    """
    Evaluates purchase against category bounded autonomy rules:
    - Groceries: <= 3k -> AUTO APPROVE
    - Electronics: <= 10k -> AUTO APPROVE
    - Electronics: > 10k -> ASK USER
    - Hard Ceiling: > 150k -> BLOCK
    """
    decision = DelegatedAuthPolicyEngine.evaluate_transaction(req)
    add_audit_log(
        action_type="DELEGATED_AUTH_EVAL",
        actor="AGENT",
        payload_summary=f"Evaluated '{req.item_title}' (₹{req.price_inr:,.2f}) -> {decision.action.value}",
        policy_verified=decision.is_within_policy
    )
    return decision

@app.post("/api/payment/sandbox/execute-charge", response_model=SandboxChargeResponse)
async def execute_sandbox_charge(req: SandboxChargeRequest):
    """Executes settled payment through simulated payment sandbox using delegated token."""
    res = PaymentWalletSandbox.execute_sandbox_charge(req)
    add_audit_log(
        action_type="SANDBOX_PAYMENT_SETTLED",
        actor="PAYMENT_AGENT",
        payload_summary=f"Settled payment for {req.item_title} (₹{req.amount:,.2f}) via {res.payment_method_used}",
        policy_verified=True
    )
    return res

# -------------------------------------------------------------
# 8. Agent Security & Untrusted Content Sanitizer Endpoints
# -------------------------------------------------------------
from backend.trust_safety.untrusted_content_sanitizer import (
    UntrustedContentSanitizer, SanitizationResult
)

class SanitizeContentRequest(BaseModel):
    raw_content: str
    merchant_name: Optional[str] = "Untrusted Merchant"
    source_field: Optional[str] = "product_description"

@app.post("/api/security/sanitize-content", response_model=SanitizationResult)
async def sanitize_untrusted_content(req: SanitizeContentRequest):
    """
    Sanitizes untrusted merchant content, stripping indirect prompt injections
    and preserving strict policy boundaries.
    """
    return UntrustedContentSanitizer.sanitize_merchant_content(
        raw_text=req.raw_content,
        merchant_name=req.merchant_name or "Untrusted Merchant",
        source_field=req.source_field or "product_description"
    )

# -------------------------------------------------------------
# 9. Tool Permissions & Agent RBAC Matrix Endpoints
# -------------------------------------------------------------
from backend.trust_safety.agent_permissions import (
    AgentPermissionGuard, AgentRole, ToolCategory, ToolInvocationCheckResult, REGISTERED_TOOLS
)

class CheckToolPermissionRequest(BaseModel):
    agent_role: AgentRole
    tool_name: str

@app.get("/api/security/permissions/matrix")
async def get_tool_permission_matrix():
    """Retrieve the full Tool Permission Matrix across all agent roles."""
    return {
        "matrix": AgentPermissionGuard.get_permission_matrix(),
        "tools": {name: t.model_dump() for name, t in REGISTERED_TOOLS.items()}
    }

@app.post("/api/security/permissions/check", response_model=ToolInvocationCheckResult)
async def check_agent_tool_permission(req: CheckToolPermissionRequest):
    """Checks if an agent role has permission to execute a specific tool."""
    return AgentPermissionGuard.check_permission(req.agent_role, req.tool_name)

# -------------------------------------------------------------
# 10. Failure Recovery & Resiliency Endpoints
# -------------------------------------------------------------
from backend.infrastructure.failure_recovery_engine import (
    FailureRecoveryEngine, FailureScenarioType, FailureRecoveryTrace
)

class SimulateFailureRequest(BaseModel):
    scenario: FailureScenarioType
    session_id: Optional[str] = "session_default"

@app.get("/api/resilience/scenarios")
async def get_resilience_scenarios():
    """Retrieve supported failure scenarios and recovery strategies."""
    return FailureRecoveryEngine.get_supported_scenarios()

@app.post("/api/resilience/simulate", response_model=FailureRecoveryTrace)
async def simulate_failure_recovery(req: SimulateFailureRequest):
    """Simulates a distributed commerce failure and returns the autonomous recovery trace."""
    return FailureRecoveryEngine.simulate_recovery(req.scenario, req.session_id or "session_default")

# -------------------------------------------------------------
# 11. Multi-Tier Memory Subsystem Endpoints
# -------------------------------------------------------------
from backend.agent.memory_manager import (
    MemoryManager, UserProfileMemory, SemanticMemoryItem, SemanticSearchResult
)

class SemanticSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

class AddSemanticMemoryRequest(BaseModel):
    content: str
    category: Optional[str] = "user_preference"

@app.get("/api/memory/overview")
async def get_memory_overview():
    """Retrieve full state of all 4 memory tiers."""
    return MemoryManager.get_all_memory()

@app.post("/api/memory/semantic/search", response_model=List[SemanticSearchResult])
async def search_semantic_memories(req: SemanticSearchRequest):
    """Vector similarity search against natural language preference memory."""
    return MemoryManager.search_semantic_memory(req.query, req.top_k or 3)

@app.post("/api/memory/semantic/add", response_model=SemanticMemoryItem)
async def add_semantic_memory(req: AddSemanticMemoryRequest):
    """Ingest a new natural language rule or preference into the Vector DB."""
    return MemoryManager.add_semantic_memory(req.content, req.category or "user_preference")

@app.put("/api/memory/preferences", response_model=UserProfileMemory)
async def update_profile_preferences(req: Dict[str, Any]):
    """Update Tier 1 User Profile Memory preferences."""
    return MemoryManager.update_profile(req)

# -------------------------------------------------------------
# 12. Agent Observability & Telemetry Endpoints
# -------------------------------------------------------------
from backend.agent.observability import (
    AgentObservabilityEngine, ObservabilityTraceResponse
)

@app.get("/api/observability/latest", response_model=ObservabilityTraceResponse)
async def get_latest_observability_trace():
    """Retrieve operational execution trace and metrics KPI summary."""
    return AgentObservabilityEngine.get_latest_session_trace()

# Health endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "system": "AgentCart Autonomous AI Shopping & Checkout",
        "brain": "Hierarchical Multi-Agent Architecture",
        "specialized_agents": ["Agent 1: Intent Agent", "Agent 2: Planning Agent", "Agent 3: Discovery Agent"],
        "merchant_apis": ["Merchant A (TechHub)", "Merchant B (ElectroBazaar)", "Merchant C (OmniStore)", "Merchant D (ProHardware)"],
        "payment_architecture": "Tokenized Delegated Authorization Sandbox (Zero Raw Card Storage)",
        "security": "Untrusted Context Sanitizer & Agent Tool Permission Matrix (RBAC)",
        "resiliency": "Distributed Failure Recovery & Autonomous Replanning Engine (6 Scenarios)",
        "memory": "4-Tier Architecture (Profile, Transactions, Working State, Vector DB)",
        "observability": "Operational Waterfall Execution Trace & Telemetry KPI Dashboard",
        "layers": ["UX", "Intelligence", "Protocol", "Infrastructure", "Trust&Safety"],
        "merchants_online": len(get_all_merchants())
    }
