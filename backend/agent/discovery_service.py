"""
Phase 3 Step 4: Multi-Merchant Product Discovery Service
Federates product discovery across Amazon, Flipkart, and Croma via CommerceGateway/CatalogTools.
Guarantees merchant isolation, bounded per-merchant timeouts, partial failure tolerance,
canonical normalization, and indirect prompt injection sanitization.
"""
from datetime import datetime, timezone
from decimal import Decimal
import logging
import time
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.orm import Session

from backend.domain.marketplace import ProductSortOption
from backend.domain.agent_schemas import (
    ShoppingIntent, DiscoveryRequest, DiscoveryResult,
    MerchantDiscoveryStatus, NormalizedProductCandidate, CanonicalProduct
)
from backend.agent.tools.catalog_tools import CatalogTools
from backend.agent.product_normalizer import ProductNormalizer

logger = logging.getLogger("agentcart.agent.discovery")

SUPPORTED_MERCHANTS = ["AMAZON", "FLIPKART", "CROMA"]


class DiscoveryService:
    """
    Federated Multi-Merchant Discovery Service.
    Orchestrates search across Amazon, Flipkart, and Croma, tracks per-merchant status,
    handles timeouts/partial failures gracefully, and normalizes candidate products.
    """

    @classmethod
    def discover(
        cls,
        db: Session,
        request: Optional[DiscoveryRequest] = None,
        intent: Optional[ShoppingIntent] = None,
        merchants: Optional[List[str]] = None,
        query: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        in_stock_only: bool = False,
        merchant_fail_simulations: Optional[Dict[str, str]] = None  # For testing: {"CROMA": "TIMEOUT"}
    ) -> DiscoveryResult:
        """
        Executes multi-merchant discovery across supported merchants.
        """
        start_time = time.perf_counter()
        
        # 1. Resolve effective intent and search query
        effective_intent = intent or (request.intent if request else None)
        
        if effective_intent:
            search_query = effective_intent.query or effective_intent.raw_query or query
            search_category = effective_intent.category or category
            budget_max = effective_intent.budget_max
            budget_min = effective_intent.budget_min
            require_stock = effective_intent.require_in_stock
        elif request:
            search_query = request.get_search_query()
            search_category = request.category or category
            budget_max = None
            budget_min = None
            require_stock = request.in_stock_only
        else:
            search_query = query
            search_category = category
            budget_max = None
            budget_min = None
            require_stock = in_stock_only

        # 2. Resolve Target Merchants
        target_merchants = cls._resolve_target_merchants(
            request=request,
            intent=effective_intent,
            explicit_merchants=merchants
        )

        merchants_attempted: List[str] = list(target_merchants)
        merchants_succeeded: List[str] = []
        merchants_failed: List[Dict[str, Any]] = []
        merchant_statuses: List[MerchantDiscoveryStatus] = []
        all_candidates: List[NormalizedProductCandidate] = []
        errors: List[str] = []

        # 3. Perform Merchant Discovery per Target Merchant
        for m_code in target_merchants:
            m_start = time.perf_counter()
            
            # Check test simulations
            if merchant_fail_simulations and m_code in merchant_fail_simulations:
                sim_err = merchant_fail_simulations[m_code]
                m_elapsed = int((time.perf_counter() - m_start) * 1000)
                status_obj = MerchantDiscoveryStatus(
                    merchant=m_code,
                    status=sim_err.upper(),
                    result_count=0,
                    error=f"Simulated {sim_err} for merchant {m_code}",
                    latency_ms=m_elapsed
                )
                merchant_statuses.append(status_obj)
                merchants_failed.append({
                    "merchant": m_code,
                    "status": sim_err.upper(),
                    "error": status_obj.error
                })
                errors.append(f"Merchant '{m_code}' failed: {sim_err}")
                continue

            try:
                # Query merchant catalog via sandboxed CatalogTools
                search_res = CatalogTools.search_multi_merchant_catalog(
                    db=db,
                    merchant_code=m_code,
                    category=search_category,
                    query=search_query,
                    max_price=budget_max,
                    min_price=budget_min,
                    in_stock_only=require_stock,
                    page=page,
                    page_size=page_size
                )
                
                # Normalize candidates safely
                merchant_candidates: List[NormalizedProductCandidate] = []
                for raw_item in search_res.items:
                    try:
                        cand = ProductNormalizer.normalize_candidate(raw_item)
                        merchant_candidates.append(cand)
                    except Exception as norm_err:
                        logger.warning("Failed to normalize merchant candidate item: %s", norm_err)
                        # Malformed product item does not crash other products
                        continue

                m_elapsed = int((time.perf_counter() - m_start) * 1000)
                merchants_succeeded.append(m_code)
                all_candidates.extend(merchant_candidates)
                
                merchant_statuses.append(MerchantDiscoveryStatus(
                    merchant=m_code,
                    status="SUCCESS",
                    result_count=len(merchant_candidates),
                    error=None,
                    latency_ms=m_elapsed
                ))

            except Exception as e:
                m_elapsed = int((time.perf_counter() - m_start) * 1000)
                err_msg = str(e)
                err_status = "TIMEOUT" if "timeout" in err_msg.lower() else "FAILED"
                
                merchants_failed.append({
                    "merchant": m_code,
                    "status": err_status,
                    "error": err_msg
                })
                merchant_statuses.append(MerchantDiscoveryStatus(
                    merchant=m_code,
                    status=err_status,
                    result_count=0,
                    error=err_msg,
                    latency_ms=m_elapsed
                ))
                errors.append(f"Discovery failed on merchant {m_code}: {err_msg}")

        # 4. Group into Canonical Products
        canonical_prods = ProductNormalizer.group_canonical_products(all_candidates)

        total_elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        is_partial = len(merchants_failed) > 0 and len(merchants_succeeded) > 0

        return DiscoveryResult(
            products=all_candidates,
            canonical_products=canonical_prods,
            merchants_attempted=merchants_attempted,
            merchants_succeeded=merchants_succeeded,
            merchants_failed=merchants_failed,
            merchant_statuses=merchant_statuses,
            total_results=len(all_candidates),
            partial_results=is_partial,
            errors=errors,
            execution_time_ms=total_elapsed_ms
        )

    @classmethod
    def _resolve_target_merchants(
        cls,
        request: Optional[DiscoveryRequest],
        intent: Optional[ShoppingIntent],
        explicit_merchants: Optional[List[str]]
    ) -> List[str]:
        """
        Determines target merchant scope.
        - Hard restriction: only search specified merchants.
        - Soft preference: search ALL active supported merchants (preference is used in ranking).
        - Default: search all supported merchants (Amazon, Flipkart, Croma).
        """
        # 1. Explicit merchant list in function call
        if explicit_merchants:
            valid = [m.upper() for m in explicit_merchants if m.upper() in SUPPORTED_MERCHANTS]
            if valid:
                return valid

        # 2. Explicit merchant list in DiscoveryRequest
        if request and request.merchants:
            valid = [m.upper() for m in request.merchants if m.upper() in SUPPORTED_MERCHANTS]
            if valid:
                return valid

        # 3. Hard merchant constraints in ShoppingIntent (if any)
        if intent:
            hard_merchants = [
                c.target_value for c in intent.spec_constraints 
                if c.key == "merchant" and c.is_hard_constraint and isinstance(c.target_value, str)
            ]
            if hard_merchants:
                valid = [m.upper() for m in hard_merchants if m.upper() in SUPPORTED_MERCHANTS]
                if valid:
                    return valid

        # 4. Note on soft preferences: If intent.merchant_preferences is set, we still return ALL supported merchants.
        # Soft preference gives a boost during MCDA ranking in Step 5, it does NOT exclude merchants during discovery.
        return list(SUPPORTED_MERCHANTS)
