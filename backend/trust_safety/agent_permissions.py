"""
Layer 5: Trust & Safety - Agent Tool Permission Matrix (RBAC)
Enforces runtime authorization boundaries across specialized agents.

Tool Permission Matrix:
                 Search Cart Checkout Payment
------------------------------------------------
Discovery Agent    ✓     ✗       ✗       ✗
Ranking Agent      ✓     ✗       ✗       ✗
Cart Agent         ✓     ✓       ✗       ✗
Checkout Agent     ✓     ✓       ✓       ✗
Payment Agent      ✗     ✗       ✓       ✓
Order Agent        ✗     ✗       ✗       ✗

Even if the LLM gets confused:
Discovery Agent cannot make payments.
"""
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

from backend.trust_safety.policy_engine import add_audit_log

class AgentRole(str, Enum):
    DISCOVERY_AGENT = "Discovery Agent"
    RANKING_AGENT = "Ranking Agent"
    CART_AGENT = "Cart Agent"
    CHECKOUT_AGENT = "Checkout Agent"
    PAYMENT_AGENT = "Payment Agent"
    ORDER_AGENT = "Order Agent"

class ToolCategory(str, Enum):
    SEARCH = "Search"
    CART = "Cart"
    CHECKOUT = "Checkout"
    PAYMENT = "Payment"

class ToolDefinition(BaseModel):
    tool_name: str
    category: ToolCategory
    description: str

class ToolInvocationCheckResult(BaseModel):
    allowed: bool
    agent_role: AgentRole
    tool_name: str
    tool_category: ToolCategory
    message: str
    security_breach_prevented: bool = False

# Exact Tool Definitions
REGISTERED_TOOLS: Dict[str, ToolDefinition] = {
    # Search Tools
    "search_products": ToolDefinition(tool_name="search_products", category=ToolCategory.SEARCH, description="Search multi-merchant product catalogs"),
    "get_product_specs": ToolDefinition(tool_name="get_product_specs", category=ToolCategory.SEARCH, description="Retrieve hardware specifications & stock levels"),
    "compare_products": ToolDefinition(tool_name="compare_products", category=ToolCategory.SEARCH, description="MCDA multi-criteria product comparison"),

    # Cart Tools
    "create_cart": ToolDefinition(tool_name="create_cart", category=ToolCategory.CART, description="Initialize a shopping cart"),
    "add_to_cart": ToolDefinition(tool_name="add_to_cart", category=ToolCategory.CART, description="Add items to merchant cart"),
    "update_cart_quantity": ToolDefinition(tool_name="update_cart_quantity", category=ToolCategory.CART, description="Modify item quantities in cart"),
    "clear_cart": ToolDefinition(tool_name="clear_cart", category=ToolCategory.CART, description="Empty all items from cart"),

    # Checkout Tools
    "create_checkout_quote": ToolDefinition(tool_name="create_checkout_quote", category=ToolCategory.CHECKOUT, description="Generate binding price quote with taxes & promos"),
    "apply_discount_coupon": ToolDefinition(tool_name="apply_discount_coupon", category=ToolCategory.CHECKOUT, description="Apply negotiated merchant discount promo"),
    "evaluate_spending_policy": ToolDefinition(tool_name="evaluate_spending_policy", category=ToolCategory.CHECKOUT, description="Evaluate budget ceiling and PIN requirement"),

    # Payment Tools
    "issue_delegated_token": ToolDefinition(tool_name="issue_delegated_token", category=ToolCategory.PAYMENT, description="Issue single-use delegated authorization mandate"),
    "authorize_payment": ToolDefinition(tool_name="authorize_payment", category=ToolCategory.PAYMENT, description="Authorize tokenized payment on bank rails"),
    "execute_sandbox_charge": ToolDefinition(tool_name="execute_sandbox_charge", category=ToolCategory.PAYMENT, description="Execute final monetary settlement")
}

# The Exact Tool Permission Matrix
TOOL_PERMISSION_MATRIX: Dict[AgentRole, Dict[ToolCategory, bool]] = {
    AgentRole.DISCOVERY_AGENT: {
        ToolCategory.SEARCH: True,
        ToolCategory.CART: False,
        ToolCategory.CHECKOUT: False,
        ToolCategory.PAYMENT: False
    },
    AgentRole.RANKING_AGENT: {
        ToolCategory.SEARCH: True,
        ToolCategory.CART: False,
        ToolCategory.CHECKOUT: False,
        ToolCategory.PAYMENT: False
    },
    AgentRole.CART_AGENT: {
        ToolCategory.SEARCH: True,
        ToolCategory.CART: True,
        ToolCategory.CHECKOUT: False,
        ToolCategory.PAYMENT: False
    },
    AgentRole.CHECKOUT_AGENT: {
        ToolCategory.SEARCH: True,
        ToolCategory.CART: True,
        ToolCategory.CHECKOUT: True,
        ToolCategory.PAYMENT: False
    },
    AgentRole.PAYMENT_AGENT: {
        ToolCategory.SEARCH: False,
        ToolCategory.CART: False,
        ToolCategory.CHECKOUT: True,
        ToolCategory.PAYMENT: True
    },
    AgentRole.ORDER_AGENT: {
        ToolCategory.SEARCH: False,
        ToolCategory.CART: False,
        ToolCategory.CHECKOUT: False,
        ToolCategory.PAYMENT: False
    }
}

class AgentPermissionGuard:
    @classmethod
    def get_permission_matrix(cls) -> Dict[str, Dict[str, bool]]:
        """Returns the serialized RBAC matrix."""
        return {
            agent.value: {cat.value: allowed for cat, allowed in perms.items()}
            for agent, perms in TOOL_PERMISSION_MATRIX.items()
        }

    @classmethod
    def check_permission(cls, agent_role: AgentRole, tool_name: str) -> ToolInvocationCheckResult:
        """
        Validates if an agent role has authorization to execute the specified tool.
        """
        tool = REGISTERED_TOOLS.get(tool_name)
        if not tool:
            # Fallback for dynamic/unregistered tools
            category = ToolCategory.SEARCH
            if "cart" in tool_name:
                category = ToolCategory.CART
            elif "checkout" in tool_name or "quote" in tool_name:
                category = ToolCategory.CHECKOUT
            elif "pay" in tool_name or "charge" in tool_name or "token" in tool_name:
                category = ToolCategory.PAYMENT
            tool = ToolDefinition(tool_name=tool_name, category=category, description="Dynamic tool")

        allowed = TOOL_PERMISSION_MATRIX[agent_role].get(tool.category, False)

        if allowed:
            return ToolInvocationCheckResult(
                allowed=True,
                agent_role=agent_role,
                tool_name=tool_name,
                tool_category=tool.category,
                message=f"✓ PERMITTED: {agent_role.value} is authorized to invoke '{tool_name}' ({tool.category.value} tool).",
                security_breach_prevented=False
            )
        else:
            # Log blocked unauthorized attempt in cryptographic ledger
            add_audit_log(
                action_type="UNAUTHORIZED_TOOL_BLOCKED",
                actor=agent_role.value,
                payload_summary=f"Security Guard blocked {agent_role.value} from unauthorized execution of '{tool_name}' ({tool.category.value} tool).",
                policy_verified=True
            )

            return ToolInvocationCheckResult(
                allowed=False,
                agent_role=agent_role,
                tool_name=tool_name,
                tool_category=tool.category,
                message=f"🛑 PERMISSION DENIED: {agent_role.value} does NOT have permission to invoke '{tool_name}' ({tool.category.value} category). Access blocked by security boundary.",
                security_breach_prevented=True
            )
