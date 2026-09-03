"""
Test Suite for 8. Tool Permissions (Agent RBAC Matrix & Tool Invocation Guardrails)
"""
import pytest
from backend.trust_safety.agent_permissions import (
    AgentPermissionGuard, AgentRole, ToolCategory
)

def test_discovery_agent_permissions():
    # Discovery Agent: Search ✓, Cart ✗, Checkout ✗, Payment ✗
    res_search = AgentPermissionGuard.check_permission(AgentRole.DISCOVERY_AGENT, "search_products")
    assert res_search.allowed is True
    assert res_search.security_breach_prevented is False

    res_cart = AgentPermissionGuard.check_permission(AgentRole.DISCOVERY_AGENT, "add_to_cart")
    assert res_cart.allowed is False
    assert res_cart.security_breach_prevented is True

    res_checkout = AgentPermissionGuard.check_permission(AgentRole.DISCOVERY_AGENT, "create_checkout_quote")
    assert res_checkout.allowed is False
    assert res_checkout.security_breach_prevented is True

    # Critical Security Invariant: Discovery Agent cannot make payments
    res_payment = AgentPermissionGuard.check_permission(AgentRole.DISCOVERY_AGENT, "authorize_payment")
    assert res_payment.allowed is False
    assert res_payment.security_breach_prevented is True
    assert "PERMISSION DENIED" in res_payment.message

def test_ranking_agent_permissions():
    # Ranking Agent: Search ✓, Cart ✗, Checkout ✗, Payment ✗
    res_search = AgentPermissionGuard.check_permission(AgentRole.RANKING_AGENT, "compare_products")
    assert res_search.allowed is True

    res_cart = AgentPermissionGuard.check_permission(AgentRole.RANKING_AGENT, "add_to_cart")
    assert res_cart.allowed is False

    res_payment = AgentPermissionGuard.check_permission(AgentRole.RANKING_AGENT, "execute_sandbox_charge")
    assert res_payment.allowed is False

def test_cart_agent_permissions():
    # Cart Agent: Search ✓, Cart ✓, Checkout ✗, Payment ✗
    res_search = AgentPermissionGuard.check_permission(AgentRole.CART_AGENT, "get_product_specs")
    assert res_search.allowed is True

    res_cart = AgentPermissionGuard.check_permission(AgentRole.CART_AGENT, "add_to_cart")
    assert res_cart.allowed is True

    res_checkout = AgentPermissionGuard.check_permission(AgentRole.CART_AGENT, "create_checkout_quote")
    assert res_checkout.allowed is False

    res_payment = AgentPermissionGuard.check_permission(AgentRole.CART_AGENT, "authorize_payment")
    assert res_payment.allowed is False

def test_checkout_agent_permissions():
    # Checkout Agent: Search ✓, Cart ✓, Checkout ✓, Payment ✗
    res_search = AgentPermissionGuard.check_permission(AgentRole.CHECKOUT_AGENT, "search_products")
    assert res_search.allowed is True

    res_cart = AgentPermissionGuard.check_permission(AgentRole.CHECKOUT_AGENT, "update_cart_quantity")
    assert res_cart.allowed is True

    res_checkout = AgentPermissionGuard.check_permission(AgentRole.CHECKOUT_AGENT, "create_checkout_quote")
    assert res_checkout.allowed is True

    res_payment = AgentPermissionGuard.check_permission(AgentRole.CHECKOUT_AGENT, "authorize_payment")
    assert res_payment.allowed is False

def test_payment_agent_permissions():
    # Payment Agent: Search ✗, Cart ✗, Checkout ✓, Payment ✓
    res_search = AgentPermissionGuard.check_permission(AgentRole.PAYMENT_AGENT, "search_products")
    assert res_search.allowed is False

    res_cart = AgentPermissionGuard.check_permission(AgentRole.PAYMENT_AGENT, "add_to_cart")
    assert res_cart.allowed is False

    res_checkout = AgentPermissionGuard.check_permission(AgentRole.PAYMENT_AGENT, "create_checkout_quote")
    assert res_checkout.allowed is True

    res_payment = AgentPermissionGuard.check_permission(AgentRole.PAYMENT_AGENT, "authorize_payment")
    assert res_payment.allowed is True

    res_charge = AgentPermissionGuard.check_permission(AgentRole.PAYMENT_AGENT, "execute_sandbox_charge")
    assert res_charge.allowed is True

def test_order_agent_permissions():
    # Order Agent: Search ✗, Cart ✗, Checkout ✗, Payment ✗
    res_search = AgentPermissionGuard.check_permission(AgentRole.ORDER_AGENT, "search_products")
    assert res_search.allowed is False

    res_cart = AgentPermissionGuard.check_permission(AgentRole.ORDER_AGENT, "add_to_cart")
    assert res_cart.allowed is False

    res_payment = AgentPermissionGuard.check_permission(AgentRole.ORDER_AGENT, "authorize_payment")
    assert res_payment.allowed is False
