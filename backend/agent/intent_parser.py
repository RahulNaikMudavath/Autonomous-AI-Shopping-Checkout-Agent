"""
Phase 3: Autonomous AI Shopping Agent - Intent Parser & Unit Normalizer
Extracts structured ShoppingIntent from natural language queries.
Normalizes financial currencies and units (lakh, k, INR, GB, TB, Hz, kg).
Distinguishes between non-negotiable hard constraints and soft preferences.
"""
from decimal import Decimal
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.domain.agent_schemas import (
    ShoppingIntent, SpecificationConstraint, ConstraintOperator,
    ObjectiveType, DeliveryPreference
)
from backend.services.pricing_service import quantize_money


class IntentParser:
    """
    Robust intent extractor and technical specification parser.
    """

    @classmethod
    def parse_intent(
        cls,
        query: str,
        previous_intent: Optional[ShoppingIntent] = None
    ) -> ShoppingIntent:
        """
        Parses a user natural language query into a validated ShoppingIntent.
        Supports multi-turn refinement if previous_intent is provided.
        """
        clean_query = query.strip()
        q_lower = clean_query.lower()

        # 1. Ambiguity & Validity Check
        if not clean_query or len(clean_query) < 3 or q_lower in ["hi", "hello", "hey", "help", "test", "buy", "find", "search", "get"]:
            return ShoppingIntent(
                raw_query=clean_query,
                is_ambiguous=True,
                clarification_needed="Please describe what product you are looking for (e.g. 'Laptop for AI/ML under ₹1.2 lakh with 32GB RAM')."
            )

        # 2. Category Detection
        category = cls._detect_category(q_lower, previous_intent)

        # 3. Target Use Case Detection
        target_use_case = cls._detect_use_case(q_lower, category, previous_intent)

        # 4. Budget & Price Constraint Normalization (Lakh, K, INR)
        budget_max, budget_min = cls._extract_budget(q_lower, previous_intent)

        # 5. Technical Specifications Extraction
        spec_constraints, req_keywords, excl_keywords = cls._extract_specifications(q_lower, category, previous_intent)

        # 6. Brand & Merchant Preferences
        brand_prefs = cls._extract_brands(q_lower, previous_intent)
        merchant_prefs = cls._extract_merchants(q_lower, previous_intent)

        # 7. Objectives & Delivery Preferences
        objective, delivery_pref = cls._extract_objective_and_delivery(q_lower, previous_intent)

        # 8. Minimum Rating & In-Stock Flag
        min_rating = 4.0
        if "4.5" in q_lower or "top rated" in q_lower or "highest rated" in q_lower:
            min_rating = 4.5
        elif previous_intent:
            min_rating = previous_intent.min_rating

        require_in_stock = True
        if "include out of stock" in q_lower or "any availability" in q_lower:
            require_in_stock = False

        return ShoppingIntent(
            raw_query=clean_query,
            category=category,
            target_use_case=target_use_case,
            budget_max=budget_max,
            budget_min=budget_min,
            currency="INR",
            spec_constraints=spec_constraints,
            required_keywords=req_keywords,
            excluded_keywords=excl_keywords,
            brand_preferences=brand_prefs,
            merchant_preferences=merchant_prefs,
            delivery_preference=delivery_pref,
            min_rating=min_rating,
            require_in_stock=require_in_stock,
            objective=objective,
            is_ambiguous=False,
            clarification_needed=None
        )

    @classmethod
    def _detect_category(cls, q_lower: str, prev: Optional[ShoppingIntent]) -> str:
        if any(w in q_lower for w in ["laptop", "macbook", "notebook", "workstation", "rog", "predator", "legion", "thinkpad"]):
            return "laptops"
        if any(w in q_lower for w in ["headphone", "earphone", "audio", "anc", "sony wh", "bose", "earbuds"]):
            return "headphones"
        if any(w in q_lower for w in ["smartphone", "iphone", "galaxy", "s24", "pixel", "oneplus", "mobile"]) or re.search(r'\bphone\b', q_lower):
            return "smartphones"
        if any(w in q_lower for w in ["monitor", "display", "ultrawide", "screen", "oled", "4k monitor", "gaming monitor"]):
            return "monitors"
        if any(w in q_lower for w in ["keyboard", "mechanical keyboard", "mx keys", "keychron"]):
            return "keyboards"
        if any(w in q_lower for w in ["mouse", "mx master", "trackball", "pointing device"]):
            return "mice"
        if any(w in q_lower for w in ["tablet", "ipad", "tab", "ipad pro"]):
            return "tablets"
        if any(w in q_lower for w in ["watch", "smartwatch", "wearable", "apple watch", "galaxy watch"]):
            return "wearables"
        if any(w in q_lower for w in ["home", "alexa", "echo", "smart home", "cleaner", "dyson"]):
            return "smart_home"
        
        if prev and prev.category:
            return prev.category
        return "laptops"

    @classmethod
    def _detect_use_case(cls, q_lower: str, category: str, prev: Optional[ShoppingIntent]) -> Optional[str]:
        if any(w in q_lower for w in ["ai", "ml", "machine learning", "deep learning", "model training", "llm"]):
            return "AI/ML Development & Data Science"
        if any(w in q_lower for w in ["gaming", "esports", "fps", "rtx", "play games"]):
            return "High-End Gaming & Esports"
        if any(w in q_lower for w in ["editing", "video", "premiere", "creator", "render", "animation"]):
            return "Content Creation & Video Production"
        if any(w in q_lower for w in ["coding", "programming", "developer", "software engineering"]):
            return "Software Engineering & Productivity"
        
        if prev and prev.target_use_case:
            return prev.target_use_case
        return "General Performance & Productivity"

    @classmethod
    def _extract_budget(cls, q_lower: str, prev: Optional[ShoppingIntent]) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Extracts upper and lower price boundaries and normalizes units.
        Handles:
        - "under ₹1.2 lakh", "under 1.2L", "1.2 lac" -> Decimal("120000.00")
        - "under 80k", "80 k" -> Decimal("80000.00")
        - "under ₹1,20,000", "under 120000" -> Decimal("120000.00")
        - "between 50k and 1 lakh" -> min=50000, max=100000
        """
        budget_max: Optional[Decimal] = None
        budget_min: Optional[Decimal] = None

        # 1. Range match: "between 50k and 1.2 lakh", "50000 to 120000"
        range_match = re.search(r'(?:between|from)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(k|lakh|lac|l)?\s*(?:to|and|-)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(k|lakh|lac|l)?\b', q_lower)
        if range_match:
            min_val = float(range_match.group(1))
            min_unit = (range_match.group(2) or "").lower()
            max_val = float(range_match.group(3))
            max_unit = (range_match.group(4) or "").lower()

            min_mult = 100000.0 if "l" in min_unit else (1000.0 if "k" in min_unit else 1.0)
            max_mult = 100000.0 if "l" in max_unit else (1000.0 if "k" in max_unit else 1.0)

            budget_min = quantize_money(Decimal(str(min_val * min_mult)))
            budget_max = quantize_money(Decimal(str(max_val * max_mult)))
            return budget_max, budget_min

        # 2. Lakh / Lac upper bound match
        lakh_match = re.search(r'(?:under|<|below|budget|within|max|around)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)\b', q_lower)
        if lakh_match:
            val = float(lakh_match.group(1)) * 100000.0
            budget_max = quantize_money(Decimal(str(val)))

        # 3. K format (e.g. 80k, 120k, 35k)
        elif re.search(r'(?:under|<|below|budget|within|max|around)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*k\b', q_lower):
            k_match = re.search(r'(?:under|<|below|budget|within|max|around)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*k\b', q_lower)
            val = float(k_match.group(1)) * 1000.0
            budget_max = quantize_money(Decimal(str(val)))

        # 4. Standard comma or raw numbers: 1,20,000 or 120000
        elif re.search(r'(?:under|<|below|budget|within|max)?\s*(?:₹|rs\.?|inr)\s*(\d{2,3}(?:,\d{2,3})+|\d{4,7})\b', q_lower):
            num_match = re.search(r'(?:under|<|below|budget|within|max)?\s*(?:₹|rs\.?|inr)\s*(\d{2,3}(?:,\d{2,3})+|\d{4,7})\b', q_lower)
            raw = num_match.group(1).replace(",", "")
            budget_max = quantize_money(Decimal(raw))
        elif re.search(r'(?:under|<|below|budget|within|max)\s*(\d{2,3}(?:,\d{2,3})+|\d{4,7})\b', q_lower):
            num_match = re.search(r'(?:under|<|below|budget|within|max)\s*(\d{2,3}(?:,\d{2,3})+|\d{4,7})\b', q_lower)
            raw = num_match.group(1).replace(",", "")
            budget_max = quantize_money(Decimal(raw))

        # Fallback to previous intent if refining without new budget
        if budget_max is None and prev and prev.budget_max:
            budget_max = prev.budget_max
        if budget_min is None and prev and prev.budget_min:
            budget_min = prev.budget_min

        return budget_max, budget_min

    @classmethod
    def _extract_specifications(
        cls,
        q_lower: str,
        category: str,
        prev: Optional[ShoppingIntent]
    ) -> Tuple[List[SpecificationConstraint], List[str], List[str]]:
        constraints: List[SpecificationConstraint] = []
        req_keywords: List[str] = []
        excl_keywords: List[str] = []

        # 1. RAM Extraction
        ram_match = re.search(r'(\d+)\s*(?:gb|gigs?)\s*(?:ram|memory)?', q_lower)
        if ram_match:
            ram_val = int(ram_match.group(1))
            if ram_val in [8, 16, 18, 24, 32, 36, 48, 64, 128]:
                constraints.append(SpecificationConstraint(
                    key="ram_gb",
                    operator=ConstraintOperator.GTE,
                    target_value=ram_val,
                    is_hard_constraint=True,
                    description=f"At least {ram_val}GB RAM"
                ))

        # 2. SSD / Storage Extraction
        tb_match = re.search(r'(\d+)\s*tb\s*(?:ssd|storage|nvme|rom)?', q_lower)
        gb_ssd_match = re.search(r'(\d{3,4})\s*(?:gb|gigs?)\s*(?:ssd|storage|nvme|rom)', q_lower)
        if tb_match:
            tb_val = int(tb_match.group(1)) * 1024
            constraints.append(SpecificationConstraint(
                key="ssd_gb",
                operator=ConstraintOperator.GTE,
                target_value=tb_val,
                is_hard_constraint=True,
                description=f"At least {tb_match.group(1)}TB SSD storage"
            ))
        elif gb_ssd_match:
            ssd_val = int(gb_ssd_match.group(1))
            constraints.append(SpecificationConstraint(
                key="ssd_gb",
                operator=ConstraintOperator.GTE,
                target_value=ssd_val,
                is_hard_constraint=True,
                description=f"At least {ssd_val}GB SSD storage"
            ))

        # 3. GPU Extraction
        if any(w in q_lower for w in ["rtx", "nvidia", "geforce", "dedicated gpu", "discrete graphics"]):
            gpu_kw = "RTX"
            if "4070" in q_lower:
                gpu_kw = "4070"
            elif "4080" in q_lower:
                gpu_kw = "4080"
            elif "4090" in q_lower:
                gpu_kw = "4090"
            elif "4060" in q_lower:
                gpu_kw = "4060"

            constraints.append(SpecificationConstraint(
                key="gpu",
                operator=ConstraintOperator.CONTAINS,
                target_value=gpu_kw,
                is_hard_constraint=True,
                description=f"NVIDIA GeForce {gpu_kw} GPU"
            ))
            req_keywords.append("RTX")
        elif "apple silicon" in q_lower or "m3 max" in q_lower or "m3 pro" in q_lower or "m4" in q_lower:
            constraints.append(SpecificationConstraint(
                key="chip",
                operator=ConstraintOperator.CONTAINS,
                target_value="M3",
                is_hard_constraint=True,
                description="Apple Silicon Pro/Max Processor"
            ))

        # 4. Display & Refresh Rate
        hz_match = re.search(r'(\d{2,3})\s*hz', q_lower)
        if hz_match:
            hz_val = int(hz_match.group(1))
            constraints.append(SpecificationConstraint(
                key="refresh_rate_hz",
                operator=ConstraintOperator.GTE,
                target_value=hz_val,
                is_hard_constraint=False,
                description=f"At least {hz_val}Hz Refresh Rate"
            ))

        # 5. Display Size
        size_match = re.search(r'(\d{2}(?:\.\d)?)\s*(?:inch|\"|-inch)', q_lower)
        if size_match:
            size_val = float(size_match.group(1))
            constraints.append(SpecificationConstraint(
                key="display_size",
                operator=ConstraintOperator.GTE,
                target_value=size_val,
                is_hard_constraint=False,
                description=f"{size_val}-inch display format"
            ))

        # 6. Battery Preference (Soft)
        if any(w in q_lower for w in ["good battery", "long battery", "all day", "high battery", "battery life"]):
            constraints.append(SpecificationConstraint(
                key="battery_hours",
                operator=ConstraintOperator.GTE,
                target_value=8.0,
                is_hard_constraint=False,
                description="Extended battery endurance (>= 8 hours)"
            ))

        # 7. Inherit previous constraints if refining
        if prev and not constraints:
            constraints = prev.spec_constraints
        if prev and not req_keywords:
            req_keywords = prev.required_keywords

        return constraints, req_keywords, excl_keywords

    @classmethod
    def _extract_brands(cls, q_lower: str, prev: Optional[ShoppingIntent]) -> List[str]:
        brands = []
        known_brands = ["apple", "asus", "rog", "acer", "lenovo", "dell", "hp", "samsung", "sony", "bose", "lg", "logitech", "dyson", "delonghi"]
        for b in known_brands:
            if b in q_lower:
                brands.append(b.capitalize() if b != "rog" else "ASUS")

        if not brands and prev and prev.brand_preferences:
            brands = prev.brand_preferences
        return list(set(brands))

    @classmethod
    def _extract_merchants(cls, q_lower: str, prev: Optional[ShoppingIntent]) -> List[str]:
        merchants = []
        if "amazon" in q_lower or "prime" in q_lower:
            merchants.append("AMAZON")
        if "flipkart" in q_lower:
            merchants.append("FLIPKART")
        if "croma" in q_lower:
            merchants.append("CROMA")

        if not merchants and prev and prev.merchant_preferences:
            merchants = prev.merchant_preferences
        return merchants

    @classmethod
    def _extract_objective_and_delivery(
        cls,
        q_lower: str,
        prev: Optional[ShoppingIntent]
    ) -> Tuple[ObjectiveType, DeliveryPreference]:
        objective = ObjectiveType.BEST_VALUE
        delivery = DeliveryPreference.BALANCED

        # Delivery signals
        if any(w in q_lower for w in ["fastest delivery", "fast delivery", "express", "quickest", "same day", "tomorrow", "1-day", "1 day"]):
            delivery = DeliveryPreference.FASTEST
            objective = ObjectiveType.FASTEST_DELIVERY

        # Price / Value signals
        if any(w in q_lower for w in ["cheapest", "lowest price", "lowest cost", "budget pick", "affordable"]):
            objective = ObjectiveType.LOWEST_PRICE
        elif any(w in q_lower for w in ["highest performance", "max performance", "fastest laptop", "most powerful", "beast"]):
            objective = ObjectiveType.MAX_PERFORMANCE
        elif any(w in q_lower for w in ["top rated", "highest rated", "best reviews"]):
            objective = ObjectiveType.HIGHEST_RATED
        elif any(w in q_lower for w in ["best value", "value for money", "bang for buck", "best deal"]):
            objective = ObjectiveType.BEST_VALUE

        if objective == ObjectiveType.BEST_VALUE and prev:
            objective = prev.objective
        if delivery == DeliveryPreference.BALANCED and prev:
            delivery = prev.delivery_preference

        return objective, delivery
