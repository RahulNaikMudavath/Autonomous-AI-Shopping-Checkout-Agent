"""
Layer 3: Commerce Protocol - Universal Commerce Protocol (UCP v1.0) & Agent Commerce Protocol (ACP)
Provides standardized agent-to-merchant discovery, quoting, tokenized checkout, and order endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from backend.schemas import (
    UCPCatalogSearchRequest, UCPCatalogResponse, Product, Merchant, CheckoutQuote, Order
)
from backend.infrastructure.merchants import get_all_merchants, get_merchant_by_id, search_merchant_catalog
from backend.infrastructure.cart_order_engine import (
    get_or_create_cart, add_to_cart, create_checkout_quote, execute_order_checkout,
    get_order_by_id, get_all_orders, process_return_request
)
from backend.trust_safety.policy_engine import evaluate_spending_policy, add_audit_log

ucp_router = APIRouter(prefix="/ucp/v1", tags=["Universal Commerce Protocol"])

class QuoteRequest(BaseModel):
    cart_id: str
    product_id: str
    quantity: int = 1

class CheckoutAuthorizationRequest(BaseModel):
    quote_id: str
    user_authorized: bool = True
    auth_token: Optional[str] = "AUTH_TOKEN_PIN_SECURE_991"
    shipping_address: Optional[str] = "Rahul N., Flat 402, HighTech Tech Park, Bangalore 560100"

class ReturnRequest(BaseModel):
    reason: str

@ucp_router.get("/merchants", response_model=List[Merchant])
async def list_ucp_merchants():
    """Discover registered merchants supporting UCP v1.0."""
    return get_all_merchants()

@ucp_router.post("/catalog/search", response_model=UCPCatalogResponse)
async def search_ucp_catalog(req: UCPCatalogSearchRequest):
    """Search unified catalog across all participating UCP merchants."""
    min_ram = None
    gpu_filter = None
    if req.specs_filter:
        min_ram = req.specs_filter.get("min_ram")
        gpu_filter = req.specs_filter.get("gpu")
        
    products = search_merchant_catalog(
        query=req.query,
        category=req.category,
        max_price=req.max_price,
        min_ram=min_ram,
        gpu_filter=gpu_filter
    )
    
    merchants = list(set(p.merchant_name for p in products))
    
    return UCPCatalogResponse(
        protocol_version="UCP/1.0",
        total_count=len(products),
        merchants_polled=merchants,
        products=products
    )

@ucp_router.post("/cart/quote", response_model=CheckoutQuote)
async def generate_ucp_quote(req: QuoteRequest):
    """Generate a tokenized checkout quote with active discounts and policy verification."""
    # Find product
    products = search_merchant_catalog()
    product = next((p for p in products if p.id == req.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # Add to cart
    cart = add_to_cart(req.cart_id, product, req.quantity)
    
    # Evaluate policy
    policy_res = evaluate_spending_policy(product)
    
    quote = create_checkout_quote(cart.cart_id, policy_res)
    
    add_audit_log(
        action_type="QUOTE_GENERATED",
        actor="AGENT",
        payload_summary=f"Created UCP Quote {quote.quote_id} for ₹{quote.amount_inr:,.2f}",
        policy_verified=policy_res.passed
    )
    
    return quote

@ucp_router.post("/checkout/execute", response_model=Order)
async def execute_ucp_checkout(req: CheckoutAuthorizationRequest):
    """Execute autonomous checkout using tokenized credentials and cryptographic audit stamp."""
    # Find quote/product
    products = search_merchant_catalog()
    # In a simulated flow, grab the top product or first
    product = products[0]
    
    # Check policy
    policy_res = evaluate_spending_policy(product)
    if not policy_res.passed:
        raise HTTPException(status_code=400, detail=f"Policy violation: {'; '.join(policy_res.policy_violations)}")
        
    # Audit log block
    audit_block = add_audit_log(
        action_type="CHECKOUT_EXECUTED",
        actor="AGENT",
        payload_summary=f"Executed checkout for {product.title} at ₹{product.price_inr:,.2f}. Merchant: {product.merchant_name}",
        policy_verified=True
    )
    
    order = execute_order_checkout(
        product=product,
        payment_method="UPI (Tokenized via UCP)",
        shipping_address=req.shipping_address or "Rahul N., Flat 402, HighTech Tech Park, Bangalore 560100",
        audit_hash=audit_block.current_hash
    )
    
    return order

@ucp_router.get("/orders/{order_id}", response_model=Order)
async def get_ucp_order(order_id: str):
    """Track real-time order lifecycle status."""
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@ucp_router.post("/orders/{order_id}/returns", response_model=Order)
async def return_ucp_order(order_id: str, req: ReturnRequest):
    """Process an autonomous return request."""
    order = process_return_request(order_id, req.reason)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    add_audit_log(
        action_type="RETURN_REQUESTED",
        actor="USER",
        payload_summary=f"Return initiated for Order {order_id}. Reason: {req.reason}",
        policy_verified=True
    )
    return order
