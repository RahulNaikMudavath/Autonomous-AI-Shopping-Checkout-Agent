"""
Layer 2: Agent Brain - Intent Extractor
Extracts structured intent, technical constraints, priorities, and multi-turn refinements.
"""
import re
from typing import Optional, Dict, Any
from backend.schemas import UserRequirements
from backend.agent.context_store import ContextStore

class IntentExtractor:
    @staticmethod
    def extract_intent_and_constraints(query: str, session_id: str = "session_default") -> Tuple_Result:
        """
        Parses user query, merging with previous session requirements for multi-turn conversations.
        """
        q_lower = query.lower()
        session = ContextStore.get_or_create_session(session_id)
        prev_reqs = session.active_requirements

        # 1. Classify Action Type
        action_type = "NEW_SEARCH"
        if any(w in q_lower for w in ["buy", "order now", "purchase", "checkout"]):
            action_type = "DIRECT_PURCHASE"
        elif any(w in q_lower for w in ["compare", "vs", "difference"]):
            action_type = "COMPARE_SPECIFIC"
        elif any(w in q_lower for w in ["track", "where is my", "order status"]):
            action_type = "ORDER_QUERY"
        elif prev_reqs and any(w in q_lower for w in ["make it", "instead", "change to", "also", "with"]):
            action_type = "REFINE_CRITERIA"

        # 2. Extract Budget (e.g. "1.2 lakh", "120000", "1.2L", "80k")
        budget = prev_reqs.budget_max_inr if (prev_reqs and action_type == "REFINE_CRITERIA") else 150000.0
        
        lakh_match = re.search(r'(?:under|<|below|budget|within)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)\b', q_lower)
        k_match = re.search(r'(?:under|<|below|budget|within)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:k)\b', q_lower)
        num_match = re.search(r'(?:under|<|below|budget|within)?\s*(?:₹|rs\.?|inr)?\s*(\d{2,3}(?:,\d{3})+|\d{5,7})\b', q_lower)
        
        if lakh_match:
            budget = float(lakh_match.group(1)) * 100000.0
        elif k_match:
            budget = float(k_match.group(1)) * 1000.0
        elif num_match:
            budget = float(num_match.group(1).replace(",", ""))
        elif "1.2" in q_lower and "lakh" in q_lower:
            budget = 120000.0

        # 3. Extract RAM
        min_ram = prev_reqs.min_ram_gb if (prev_reqs and action_type == "REFINE_CRITERIA") else 16
        ram_match = re.search(r'(\d+)\s*gb\s*ram', q_lower)
        if ram_match:
            min_ram = int(ram_match.group(1))
        elif "32gb" in q_lower or "32 gb" in q_lower:
            min_ram = 32
        elif "64gb" in q_lower or "64 gb" in q_lower:
            min_ram = 64
        elif "16gb" in q_lower or "16 gb" in q_lower:
            min_ram = 16

        # 4. Extract GPU
        gpu_brand = prev_reqs.gpu_brand_preference if (prev_reqs and action_type == "REFINE_CRITERIA") else "NVIDIA"
        if "nvidia" in q_lower or "rtx" in q_lower or "geforce" in q_lower:
            gpu_brand = "NVIDIA"
        elif "amd" in q_lower or "radeon" in q_lower:
            gpu_brand = "AMD"
        elif "apple" in q_lower or "m3" in q_lower or "mac" in q_lower:
            gpu_brand = "Apple"

        # 5. Extract SSD
        min_ssd = prev_reqs.min_ssd_gb if (prev_reqs and action_type == "REFINE_CRITERIA") else 512
        if "2tb" in q_lower or "2 tb" in q_lower:
            min_ssd = 2048
        elif "1tb" in q_lower or "1 tb" in q_lower:
            min_ssd = 1024
        elif "512gb" in q_lower or "512 gb" in q_lower:
            min_ssd = 512

        # 6. Extract Battery Priority
        battery_prio = prev_reqs.battery_priority if (prev_reqs and action_type == "REFINE_CRITERIA") else "medium"
        if any(w in q_lower for w in ["good battery", "high battery", "long battery", "battery life", "all day", "prefer good battery"]):
            battery_prio = "high"

        # 7. Extract Objective
        objective = prev_reqs.objective if (prev_reqs and action_type == "REFINE_CRITERIA") else "best_value"
        if "best value" in q_lower or "value" in q_lower:
            objective = "best_value"
        elif "highest performance" in q_lower or "max performance" in q_lower or "fastest" in q_lower:
            objective = "highest_performance"
        elif "cheapest" in q_lower or "lowest price" in q_lower or "budget" in q_lower:
            objective = "lowest_price"

        reqs = UserRequirements(
            raw_query=query,
            budget_max_inr=budget,
            min_ram_gb=min_ram,
            gpu_brand_preference=gpu_brand,
            min_ssd_gb=min_ssd,
            battery_priority=battery_prio,
            objective=objective,
            category="laptops",
            target_use_case="AI/ML development" if ("ai" in q_lower or "ml" in q_lower) else "General Compute"
        )

        # Update Session
        ContextStore.update_session_requirements(session_id, reqs)
        ContextStore.set_scratchpad_value(session_id, "last_action_type", action_type)

        return action_type, reqs

# Type alias helper
Tuple_Result = tuple[str, UserRequirements]
