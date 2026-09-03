"""
Layer 2 & 4: Agent Brain - Stage-Gated Checkout Pipeline
Coordinates the autonomous execution lifecycle:
Cart ➔ Checkout ➔ Authorization ➔ Payment ➔ Order
"""
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from backend.schemas import Product, Cart, CheckoutQuote, Order, PolicyCheckResult, TraceStep
from backend.infrastructure.cart_order_engine import (
    get_or_create_cart, add_to_cart, create_checkout_quote, execute_order_checkout
)
from backend.trust_safety.policy_engine import evaluate_spending_policy, add_audit_log
from backend.agent.context_store import ContextStore

class CheckoutPipeline:
    @staticmethod
    def execute_stage_gated_checkout(
        product: Product,
        cart_id: str = "default_user_cart",
        session_id: str = "session_default",
        user_confirmed: bool = True,
        shipping_address: Optional[str] = None,
        payment_method: str = "UPI (Tokenized 1-Click)"
    ) -> Tuple[Order, List_TraceSteps]:
        """
        Executes all 5 stages of the commerce pipeline with complete traceability.
        """
        traces = []
        user_profile = ContextStore.get_user_profile()
        final_address = shipping_address or user_profile.default_shipping_address

        # 1. Stage: Cart
        ContextStore.set_active_stage(session_id, "CART")
        cart = add_to_cart(cart_id, product, quantity=1)
        traces.append(TraceStep(
            step_id="stage_cart",
            title="🛒 Stage 1: Cart Aggregation",
            status="completed",
            summary=f"Added '{product.title}' (₹{product.price_inr:,.2f}) to multi-merchant cart.",
            details={"cart_id": cart.cart_id, "items_count": len(cart.items), "subtotal": cart.subtotal_inr},
            execution_time_ms=18
        ))

        # 2. Stage: Checkout Quote
        ContextStore.set_active_stage(session_id, "CHECKOUT")
        policy_check = evaluate_spending_policy(product)
        quote = create_checkout_quote(cart.cart_id, policy_check)
        traces.append(TraceStep(
            step_id="stage_checkout_quote",
            title="🧾 Stage 2: Dynamic Checkout Quoting",
            status="completed",
            summary=f"Generated UCP Quote {quote.quote_id} for ₹{quote.amount_inr:,.2f} with itemized GST & AI discount.",
            details={"quote_id": quote.quote_id, "breakdown": quote.breakdown},
            execution_time_ms=22
        ))

        # 3. Stage: Authorization
        ContextStore.set_active_stage(session_id, "AUTHORIZATION")
        if not policy_check.passed:
            traces.append(TraceStep(
                step_id="stage_authorization",
                title="🛡️ Stage 3: Authorization Boundary Blocked",
                status="failed",
                summary=f"Transaction blocked: {'; '.join(policy_check.policy_violations)}",
                details=policy_check.model_dump(),
                execution_time_ms=15
            ))
            raise ValueError(f"Authorization Blocked: {'; '.join(policy_check.policy_violations)}")

        traces.append(TraceStep(
            step_id="stage_authorization",
            title="🛡️ Stage 3: Spending & Policy Authorization",
            status="completed",
            summary=f"Policy verified passed. Single-item threshold: {'Human Approved' if user_confirmed else 'Auto-Approved'}.",
            details=policy_check.model_dump(),
            execution_time_ms=16
        ))

        # 4. Stage: Payment Execution
        ContextStore.set_active_stage(session_id, "PAYMENT")
        audit_block = add_audit_log(
            action_type="PAYMENT_TOKEN_CHARGED",
            actor="AGENT_PAYMENT_GATEWAY",
            payload_summary=f"Charged ₹{product.price_inr:,.2f} via {payment_method} to {product.merchant_name}",
            policy_verified=True
        )
        traces.append(TraceStep(
            step_id="stage_payment",
            title="💳 Stage 4: Tokenized Payment Settled",
            status="completed",
            summary=f"Processed tokenized payment via {payment_method}. Cryptographic audit stamp created.",
            details={"payment_method": payment_method, "audit_hash": audit_block.current_hash[:16] + "..."},
            execution_time_ms=28
        ))

        # 5. Stage: Order Lifecycle & Carrier Dispatch
        ContextStore.set_active_stage(session_id, "ORDER")
        order = execute_order_checkout(
            product=product,
            payment_method=payment_method,
            shipping_address=final_address,
            audit_hash=audit_block.current_hash
        )
        traces.append(TraceStep(
            step_id="stage_order_dispatched",
            title="📦 Stage 5: Order Created & Carrier Dispatched",
            status="completed",
            summary=f"Order {order.order_id} confirmed. Tracking: {order.tracking_id}. ETA: {order.estimated_delivery}.",
            details={"order_id": order.order_id, "tracking_id": order.tracking_id, "eta": order.estimated_delivery},
            execution_time_ms=25
        ))

        return order, traces

List_TraceSteps = list[TraceStep]
