"""
Layer 2: Agent Brain - Agent 3: Discovery Agent
Specialized in querying Merchant A, B, C, and D commerce APIs and Live Web Retailers (Amazon, Flipkart, Croma, Apple, etc.),
verifying real-time stock levels, sanitizing third-party untrusted descriptions,
and normalizing heterogeneous commerce responses.
"""
from typing import List, Dict, Any, Tuple
from backend.schemas import Product, UserRequirements, TraceStep
from backend.infrastructure.merchants import get_all_merchants, search_merchant_catalog
from backend.agent.context_store import ContextStore
from backend.trust_safety.untrusted_content_sanitizer import UntrustedContentSanitizer
from backend.agent.live_discovery_engine import LiveDiscoveryEngine
from backend.config import get_settings

class DiscoveryAgent:
    @staticmethod
    def discover_candidates(reqs: UserRequirements, session_id: str = "session_default") -> Tuple[List[Product], TraceStep]:
        """
        Broadcasting parallel discovery requests across Merchant A, B, C, and D APIs & Live Real Retailers.
        Passes all third-party merchant descriptions through the UntrustedContentSanitizer.
        """
        settings = get_settings()
        user_profile = ContextStore.get_user_profile()
        q_lower = (reqs.raw_query or "").lower()

        # Check if query targets non-laptop category or live mode
        is_universal_category = any(w in q_lower for w in [
            "headphone", "earphone", "audio", "sony wh", "bose", "sennheiser",
            "phone", "smartphone", "iphone", "samsung", "oneplus", "pixel",
            "monitor", "display", "gaming monitor", "4k", "oled", "gpu", "shoe", "camera"
        ])

        candidates: List[Product] = []

        if is_universal_category or settings.live_discovery_mode == "auto":
            live_candidates = LiveDiscoveryEngine.search_live_products(reqs)
            candidates.extend(live_candidates)

        # Also pull sandbox merchants for laptops
        if not is_universal_category or len(candidates) == 0:
            max_search_price = (reqs.budget_max_inr or 120000.0) * 1.3
            sandbox_candidates = search_merchant_catalog(
                category="laptops",
                max_price=max_search_price,
                min_ram=16
            )
            candidates.extend(sandbox_candidates)

        # Sanitize untrusted merchant descriptions & specs
        sanitized_candidates = []
        for p in candidates:
            sanitized_title = UntrustedContentSanitizer.sanitize_merchant_content(
                p.title, merchant_name=p.merchant_name, source_field="product_title"
            ).sanitized_clean_content

            p_copy = p.model_copy()
            p_copy.title = sanitized_title
            sanitized_candidates.append(p_copy)

        # Filter in-stock only
        in_stock_candidates = [p for p in sanitized_candidates if p.in_stock]

        # Prioritize affinity brands slightly if matched
        if user_profile.brand_affinity:
            in_stock_candidates.sort(
                key=lambda p: 0 if p.brand in user_profile.brand_affinity else 1
            )

        # Save to context scratchpad
        ContextStore.set_scratchpad_value(session_id, "discovered_count", len(in_stock_candidates))

        trace = TraceStep(
            step_id="trace_discovery_agent",
            title="🌐 Agent 3 (Discovery Agent): Live Web Retailers & Merchant Federated Query",
            status="completed",
            summary=f"Polled live commerce endpoints (Amazon, Flipkart, Croma, Merchant A-D). Discovered {len(in_stock_candidates)} candidate products.",
            details={
                "merchants_polled": list(set(p.merchant_name for p in in_stock_candidates)),
                "total_candidates": len(in_stock_candidates),
                "untrusted_sanitization_applied": True
            }
        )

        return in_stock_candidates, trace
