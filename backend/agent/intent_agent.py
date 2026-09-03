"""
Agent 1 — Intent Agent
Converts natural language queries into exact structured state:
{
  "category": "laptop",
  "budget": {
    "max": 120000,
    "currency": "INR"
  },
  "requirements": {
    "ram_gb": {
      "min": 32
    },
    "storage_gb": {
      "min": 1000
    },
    "gpu": "NVIDIA"
  },
  "optimization": "value"
}
"""
import re
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class BudgetSpec(BaseModel):
    max: float
    currency: str = "INR"

class MinConstraint(BaseModel):
    min: int

class RequirementsSpec(BaseModel):
    ram_gb: Optional[MinConstraint] = None
    storage_gb: Optional[MinConstraint] = None
    gpu: Optional[str] = None
    battery_life_hours: Optional[MinConstraint] = None

class StructuredIntentState(BaseModel):
    category: str = "laptop"
    budget: BudgetSpec
    requirements: RequirementsSpec
    optimization: str = "value"  # "value" | "performance" | "price"

class IntentAgent:
    @staticmethod
    def parse_query_to_state(query: str) -> StructuredIntentState:
        """
        Converts unstructured query (e.g. 'I need a laptop for coding and AI under 1.2L')
        into exact StructuredIntentState.
        """
        q_lower = query.lower()

        # 1. Budget extraction
        budget_val = 150000.0
        currency = "INR"
        
        lakh_match = re.search(r'(?:under|<|below|budget|within)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)\b', q_lower)
        k_match = re.search(r'(?:under|<|below|budget|within)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:k)\b', q_lower)
        num_match = re.search(r'(?:under|<|below|budget|within)?\s*(?:₹|rs\.?|inr)?\s*(\d{2,3}(?:,\d{3})+|\d{5,7})\b', q_lower)
        
        if lakh_match:
            budget_val = float(lakh_match.group(1)) * 100000.0
        elif k_match:
            budget_val = float(k_match.group(1)) * 1000.0
        elif num_match:
            budget_val = float(num_match.group(1).replace(",", ""))
        elif "1.2" in q_lower and "l" in q_lower:
            budget_val = 120000.0

        # 2. RAM extraction
        ram_val = 16
        ram_match = re.search(r'(\d+)\s*gb\s*ram', q_lower)
        if ram_match:
            ram_val = int(ram_match.group(1))
        elif "32gb" in q_lower or "32 gb" in q_lower:
            ram_val = 32
        elif "64gb" in q_lower or "64 gb" in q_lower:
            ram_val = 64
        elif "ai" in q_lower or "ml" in q_lower or "coding and ai" in q_lower:
            # Default for coding and AI workloads if under 1.2L
            ram_val = 32

        # 3. Storage extraction
        storage_val = 1000
        if "2tb" in q_lower or "2 tb" in q_lower or "2000" in q_lower:
            storage_val = 2000
        elif "1tb" in q_lower or "1 tb" in q_lower or "1000" in q_lower:
            storage_val = 1000
        elif "512gb" in q_lower or "512 gb" in q_lower:
            storage_val = 512

        # 4. GPU extraction
        gpu_brand = "NVIDIA"
        if "amd" in q_lower or "radeon" in q_lower:
            gpu_brand = "AMD"
        elif "apple" in q_lower or "m3" in q_lower:
            gpu_brand = "Apple"
        elif "nvidia" in q_lower or "rtx" in q_lower or "ai" in q_lower:
            gpu_brand = "NVIDIA"

        # 5. Optimization
        optimization = "value"
        if "performance" in q_lower or "fastest" in q_lower or "max" in q_lower:
            optimization = "performance"
        elif "cheap" in q_lower or "lowest price" in q_lower:
            optimization = "price"
        else:
            optimization = "value"

        # 6. Category
        category = "laptop"
        if "monitor" in q_lower:
            category = "monitor"
        elif "gpu" in q_lower and "laptop" not in q_lower:
            category = "gpu"

        return StructuredIntentState(
            category=category,
            budget=BudgetSpec(max=budget_val, currency=currency),
            requirements=RequirementsSpec(
                ram_gb=MinConstraint(min=ram_val),
                storage_gb=MinConstraint(min=storage_val),
                gpu=gpu_brand
            ),
            optimization=optimization
        )
