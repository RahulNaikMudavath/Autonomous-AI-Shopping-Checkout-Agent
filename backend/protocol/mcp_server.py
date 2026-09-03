"""
Layer 3: Commerce Protocol - Model Context Protocol (MCP) Tool Interface
Exposes standard MCP tool definitions that any LLM agent or MCP client can call.
"""
from typing import Dict, Any, List, Optional
from backend.schemas import MCPToolCallRequest, MCPToolCallResponse
from backend.infrastructure.merchants import search_merchant_catalog, get_all_merchants
from backend.agent.planner import extract_requirements, compute_mcda_value_score
from backend.trust_safety.policy_engine import (
    evaluate_spending_policy, get_audit_ledger, verify_audit_ledger_integrity, add_audit_log
)
from backend.infrastructure.cart_order_engine import execute_order_checkout, get_order_by_id, get_all_orders

MCP_TOOLS_SPEC = [
    {
        "name": "search_products",
        "description": "Searches multi-merchant product catalogs with budget, specs and category filters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword or user query"},
                "max_price_inr": {"type": "number", "description": "Maximum budget ceiling in INR"},
                "min_ram_gb": {"type": "integer", "description": "Minimum RAM size in GB"},
                "gpu_filter": {"type": "string", "description": "GPU filter string, e.g. 'RTX 4070'"}
            }
        }
    },
    {
        "name": "calculate_value_score",
        "description": "Computes objective Multi-Criteria Decision Analysis (MCDA) value score (1-10) for a product.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Unique product ID"},
                "budget_max_inr": {"type": "number", "description": "User budget ceiling in INR"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "verify_spending_policy",
        "description": "Verifies whether a product purchase violates spending caps or requires human approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID to verify"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "execute_checkout_order",
        "description": "Executes tokenized checkout and creates an immutable cryptographic audit record.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID to buy"},
                "shipping_address": {"type": "string", "description": "Target delivery address"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "track_order_status",
        "description": "Tracks order status and delivery updates across all merchants.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"}
            },
            "required": ["order_id"]
        }
    }
]

def handle_mcp_tool_call(req: MCPToolCallRequest) -> MCPToolCallResponse:
    """Dispatches tool execution to the appropriate AgentCart layer."""
    name = req.tool_name
    args = req.arguments
    
    try:
        if name == "search_products":
            products = search_merchant_catalog(
                query=args.get("query"),
                max_price=args.get("max_price_inr"),
                min_ram=args.get("min_ram_gb"),
                gpu_filter=args.get("gpu_filter")
            )
            return MCPToolCallResponse(
                tool_name=name,
                success=True,
                result={"count": len(products), "products": [p.model_dump() for p in products]}
            )
            
        elif name == "calculate_value_score":
            product_id = args.get("product_id")
            products = search_merchant_catalog()
            product = next((p for p in products if p.id == product_id), None)
            if not product:
                return MCPToolCallResponse(tool_name=name, success=False, result=None, error=f"Product {product_id} not found")
            reqs = extract_requirements(f"budget under {args.get('budget_max_inr', 150000)}")
            score, breakdown = compute_mcda_value_score(product, reqs)
            return MCPToolCallResponse(tool_name=name, success=True, result={"product_id": product_id, "value_score": score, "breakdown": breakdown})
            
        elif name == "verify_spending_policy":
            product_id = args.get("product_id")
            products = search_merchant_catalog()
            product = next((p for p in products if p.id == product_id), None)
            if not product:
                return MCPToolCallResponse(tool_name=name, success=False, result=None, error=f"Product {product_id} not found")
            check = evaluate_spending_policy(product)
            return MCPToolCallResponse(tool_name=name, success=True, result=check.model_dump())
            
        elif name == "execute_checkout_order":
            product_id = args.get("product_id")
            products = search_merchant_catalog()
            product = next((p for p in products if p.id == product_id), None)
            if not product:
                return MCPToolCallResponse(tool_name=name, success=False, result=None, error=f"Product {product_id} not found")
            
            audit = add_audit_log(
                action_type="MCP_TOOL_CHECKOUT",
                actor="MCP_CLIENT",
                payload_summary=f"Checkout triggered via MCP Tool for {product.title}",
                policy_verified=True
            )
            
            order = execute_order_checkout(
                product=product,
                shipping_address=args.get("shipping_address", "Default Shipping Address"),
                audit_hash=audit.current_hash
            )
            return MCPToolCallResponse(tool_name=name, success=True, result=order.model_dump())
            
        elif name == "track_order_status":
            order_id = args.get("order_id")
            order = get_order_by_id(order_id)
            if not order:
                return MCPToolCallResponse(tool_name=name, success=False, result=None, error=f"Order {order_id} not found")
            return MCPToolCallResponse(tool_name=name, success=True, result=order.model_dump())
            
        else:
            return MCPToolCallResponse(tool_name=name, success=False, result=None, error=f"Unknown tool '{name}'")
            
    except Exception as e:
        return MCPToolCallResponse(tool_name=name, success=False, result=None, error=str(e))
