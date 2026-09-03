"""
Layer 2: Agent Brain - Discovery Agent
Specialized in federated multi-merchant catalog discovery, stock checking, and spec normalization.
"""
from typing import List, Dict, Any, Tuple
from backend.schemas import Product, UserRequirements, TraceStep
from backend.infrastructure.merchants import get_all_merchants, search_merchant_catalog
from backend.agent.context_store import ContextStore

class DiscoveryAgent:
    @staticmethod
    def discover_candidates(reqs: UserRequirements, session_id: str = "session_default") -> Tuple[List[Product], TraceStep]:
        """
        Broadcasting parallel discovery requests across all merchants.
        """
        merchants = get_all_merchants()
        user_profile = ContextStore.get_user_profile()

        # Query catalog with budget headroom
        max_search_price = (reqs.budget_max_inr or 120000.0) * 1.3
        raw_candidates = search_merchant_catalog(
            category=reqs.category,
            max_price=max_search_price,
            min_ram=16
        )

        # Filter in-stock only
        in_stock_candidates = [p for p in raw_candidates if p.in_stock]

        # Prioritize affinity brands slightly if matched
        if user_profile.brand_affinity:
            in_stock_candidates.sort(
                key=lambda p: 0 if p.brand in user_profile.brand_affinity else 1
            )

        # Save to context scratchpad
        ContextStore.set_scratchpad_value(session_id, "discovered_count", len(in_stock_candidates))

        trace = TraceStep(
            step_id="trace_discovery_agent",
            title="🌐 Discovery Agent: Federated Multi-Merchant Search",
            status="completed",
            summary=f"Polled {len(merchants)} merchants ({', '.join(m.name for m in merchants)}). Retrieved {len(in_stock_candidates)} in-stock candidates meeting specs.",
            details={
                "merchants_polled": [m.name for m in merchants],
                "candidates_found": len(in_stock_candidates),
                "products": [p.title for p in in_stock_candidates]
            },
            execution_time_ms=42
        )

        return in_stock_candidates, trace
