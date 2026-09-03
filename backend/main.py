"""
AgentCart Main Application
FastAPI Server connecting all 5 layers:
- User Experience APIs
- Agent Intelligence: Hierarchical Multi-Agent Supervisor & Context Store
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
from backend.agent.supervisor import AgentSupervisor
from backend.agent.context_store import ContextStore
from backend.agent.checkout_pipeline import CheckoutPipeline
from backend.infrastructure.merchants import get_all_merchants, search_merchant_catalog
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

app = FastAPI(
    title="AgentCart - Autonomous AI Shopping & Checkout Agent",
    description="5-Layer Autonomous Commerce Intelligence System with Hierarchical Agent Brain",
    version="1.1.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Protocol Sub-router
app.include_router(ucp_router)

# Request payloads
class ChatQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "session_default"

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
# 1. Shopping Assistant & Agent Brain Endpoints
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
# 2. Cart & Commerce Infrastructure Endpoints
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
# 3. Order Lifecycle & Return Management Endpoints
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
# 4. Trust & Safety, Policies & Cryptographic Ledger Endpoints
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
# 5. MCP (Model Context Protocol) Server Tool Endpoints
# -------------------------------------------------------------

@app.get("/api/mcp/tools")
async def get_mcp_tool_definitions():
    """List all available MCP tools supported by AgentCart."""
    return {"tools": MCP_TOOLS_SPEC}

@app.post("/api/mcp/call", response_model=MCPToolCallResponse)
async def execute_mcp_tool(req: MCPToolCallRequest):
    """Directly execute an MCP tool."""
    return handle_mcp_tool_call(req)

# Health endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "system": "AgentCart Autonomous AI Shopping & Checkout",
        "brain": "Hierarchical Multi-Agent Architecture",
        "subagents": ["DiscoveryAgent", "RankingAgent", "MerchantAgent", "Supervisor"],
        "layers": ["UX", "Intelligence", "Protocol", "Infrastructure", "Trust&Safety"],
        "merchants_online": len(get_all_merchants())
    }
