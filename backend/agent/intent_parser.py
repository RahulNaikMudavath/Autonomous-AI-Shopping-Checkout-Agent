"""
Phase 3: Autonomous AI Shopping Agent - Intent Parser & Unit Normalizer
Extracts structured ShoppingIntent from natural language queries.
Normalizes financial currencies and units (lakh, lac, L, k, INR, GB, TB, Hz, W, kg).
Distinguishes between non-negotiable hard constraints and soft preferences.
Enforces strict prompt injection defenses and validation bounds.
"""
from decimal import Decimal
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.domain.agent_schemas import (
    ShoppingIntent, SpecificationConstraint, ConstraintOperator,
    ObjectiveType, DeliveryPreference
)
from backend.services.pricing_service import quantize_money
from backend.trust_safety.untrusted_content_sanitizer import UntrustedContentSanitizer


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
        if not query or not query.strip():
            raise ValueError("Query string must not be empty.")

        clean_query = query.strip()
        
        # 1. Sanitize for prompt injection attacks and adversarial directives
        san_res = UntrustedContentSanitizer.sanitize_merchant_content(
            raw_text=clean_query,
            merchant_name="UserPrompt",
            source_field="user_query"
        )
        safe_query_text = san_res.sanitized_clean_content
        q_lower = safe_query_text.lower()

        # 2. Check for negative budget inputs (must reject immediately)
        if re.search(r'-\s*(?:₹|rs\.?|inr)?\s*\d+', q_lower) or re.search(r'(?:under|<|below|budget)\s*-\s*\d+', q_lower):
            raise ValueError("budget_max cannot be negative")

        # 3. Ambiguity & Short Greeting Check
        # Generic greetings with no product context are flagged as ambiguous
        ambiguous_tokens = ["hi", "hello", "hey", "help", "test", "buy", "find", "search", "get", "show", "need"]
        words = re.findall(r'\b\w+\b', q_lower)
        if len(words) <= 2 and all(w in ambiguous_tokens for w in words):
            return ShoppingIntent(
                raw_query=clean_query,
                category="laptops",
                is_ambiguous=True,
                clarification_needed="Please describe what product you are looking for (e.g. 'Laptop for AI/ML under ₹1.2 lakh with 32GB RAM')."
            )

        # 4. Category Detection
        category = cls._detect_category(q_lower, previous_intent)

        # 5. Quantity Extraction
        quantity = cls._extract_quantity(q_lower, previous_intent)

        # 6. Target Use Case / Purpose Detection
        purpose = cls._detect_use_case(q_lower, category, previous_intent)

        # 7. Budget & Price Constraint Normalization (Lakh, K, INR, Ranges)
        budget_max, budget_min = cls._extract_budget(q_lower, previous_intent)

        # 8. Exclusions Extraction
        excl_keywords = cls._extract_exclusions(q_lower, previous_intent)

        # 9. Technical Specifications Extraction (Hard vs Soft constraints)
        spec_constraints, req_keywords = cls._extract_specifications(q_lower, category, previous_intent)

        # 10. Brand & Merchant Preferences (Soft)
        brand_prefs = cls._extract_brands(q_lower, previous_intent)
        merchant_prefs = cls._extract_merchants(q_lower, previous_intent)

        # 11. Objectives & Delivery Preferences
        objective, delivery_pref = cls._extract_objective_and_delivery(q_lower, previous_intent)

        # 12. Minimum Rating & In-Stock Flag
        min_rating = 4.0
        if "4.5" in q_lower or "top rated" in q_lower or "highest rated" in q_lower:
            min_rating = 4.5
        elif previous_intent:
            min_rating = previous_intent.min_rating

        require_in_stock = True
        if "include out of stock" in q_lower or "any availability" in q_lower:
            require_in_stock = False

        intent = ShoppingIntent(
            raw_query=clean_query,
            category=category,
            query=category,
            purpose=purpose,
            target_use_case=purpose,
            quantity=quantity,
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
        return intent

    @classmethod
    def _extract_quantity(cls, q_lower: str, prev: Optional[ShoppingIntent]) -> int:
        """
        Extracts requested unit quantity. (e.g. 'buy 2 monitors', '3 laptops', 'quantity 4')
        """
        q_match = re.search(r'(?:buy|order|need|purchase|get|quantity|qty|units?)?\s*(\d+)\s*(?:monitors?|laptops?|headphones?|phones?|smartphones?|keyboards?|mice|units?|items?|pcs?|pieces?)\b', q_lower)
        if q_match:
            val = int(q_match.group(1))
            if 1 <= val <= 100:
                return val
        
        # Word numbers
        word_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "pair": 2}
        for word, num in word_map.items():
            if re.search(rf'\b(?:buy|order|need|get)\s+{word}\b', q_lower) or re.search(rf'\b{word}\s+(?:monitors?|laptops?|headphones?|phones?|items?)\b', q_lower):
                return num

        if prev and prev.quantity > 1:
            return prev.quantity
        return 1

    @classmethod
    def _detect_category(cls, q_lower: str, prev: Optional[ShoppingIntent]) -> str:
        # Check headphone before phone to avoid substring collision
        if any(w in q_lower for w in ["headphone", "headphones", "earphone", "earphones", "earbuds", "airpods", "audio", "anc", "sony wh", "bose"]):
            return "headphones"
        if any(w in q_lower for w in ["laptop", "macbook", "notebook", "workstation", "rog", "predator", "legion", "thinkpad"]):
            return "laptops"
        if any(w in q_lower for w in ["smartphone", "smartphones", "iphone", "galaxy", "s24", "pixel", "oneplus", "mobile"]) or re.search(r'\bphones?\b', q_lower):
            return "smartphones"
        if any(w in q_lower for w in ["monitor", "monitors", "display", "ultrawide", "screen", "oled", "4k monitor", "gaming monitor"]):
            return "monitors"
        if any(w in q_lower for w in ["keyboard", "keyboards", "mechanical keyboard", "mx keys", "keychron"]):
            return "keyboards"
        if any(w in q_lower for w in ["mouse", "mice", "mx master", "trackball", "pointing device"]):
            return "mice"
        if any(w in q_lower for w in ["tablet", "tablets", "ipad", "tab", "ipad pro"]):
            return "tablets"
        if any(w in q_lower for w in ["watch", "smartwatch", "wearable", "apple watch", "galaxy watch"]):
            return "wearables"
        if any(w in q_lower for w in ["home", "alexa", "echo", "smart home", "cleaner", "dyson", "purifier"]):
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
        if any(w in q_lower for w in ["editing", "video editing", "premiere", "creator", "render", "animation", "photoshop"]):
            return "Content Creation & Video Production"
        if any(w in q_lower for w in ["coding", "programming", "developer", "software engineering", "web dev"]):
            return "Software Engineering & Productivity"
        
        if prev and (prev.purpose or prev.target_use_case):
            return prev.purpose or prev.target_use_case
        return "General Performance & Productivity"

    @classmethod
    def _extract_exclusions(cls, q_lower: str, prev: Optional[ShoppingIntent]) -> List[str]:
        excl = []
        if any(w in q_lower for w in ["no refurbished", "exclude refurbished", "not refurbished", "no renewed", "no used", "non-refurbished"]):
            excl.append("refurbished")
        if "no intel" in q_lower or "exclude intel" in q_lower:
            excl.append("intel")
        if "no amd" in q_lower or "exclude amd" in q_lower:
            excl.append("amd")
        if "no apple" in q_lower or "exclude apple" in q_lower:
            excl.append("apple")

        if prev and prev.excluded_keywords:
            excl = list(set(excl + prev.excluded_keywords))
        return excl

    @classmethod
    def _extract_budget(cls, q_lower: str, prev: Optional[ShoppingIntent]) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Extracts upper and lower price boundaries and normalizes Indian monetary units.
        Handles:
        - 'under ₹1.2 lakh', 'under 1.2L', '1.2 lac', '1.2lakhs' -> Decimal("120000.00")
        - 'under 80k', '80 k', '80 thousand' -> Decimal("80000.00")
        - 'under ₹1,20,000', 'under 120000', '120000 INR', 'Rs 120000' -> Decimal("120000.00")
        - 'between 50k and 1.2 lakh' -> min=50000, max=120000
        """
        budget_max: Optional[Decimal] = None
        budget_min: Optional[Decimal] = None

        # 1. Range match: "between 50k and 1.2 lakh", "50000 to 120000", "from 50k to 1 lakh"
        range_match = re.search(r'(?:between|from)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lac|l)?\s*(?:to|and|-)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lac|l)?\b', q_lower)
        if range_match:
            min_val = float(range_match.group(1))
            min_unit = (range_match.group(2) or "").lower()
            max_val = float(range_match.group(3))
            max_unit = (range_match.group(4) or "").lower()

            min_mult = 100000.0 if ("l" in min_unit or "lac" in min_unit or "lakh" in min_unit) else (1000.0 if ("k" in min_unit or "thousand" in min_unit) else 1.0)
            max_mult = 100000.0 if ("l" in max_unit or "lac" in max_unit or "lakh" in max_unit) else (1000.0 if ("k" in max_unit or "thousand" in max_unit) else 1.0)

            budget_min = quantize_money(Decimal(str(min_val * min_mult)))
            budget_max = quantize_money(Decimal(str(max_val * max_mult)))

            if budget_min > budget_max:
                raise ValueError(f"Impossible budget range: budget_min ({budget_min}) exceeds budget_max ({budget_max})")
            return budget_max, budget_min

        # 2. Lakh / Lac upper bound match (e.g. 1.2 lakh, 1.2L, 1.2 lac, 1 lakh)
        lakh_match = re.search(r'(?:under|<|below|budget|within|max|around|approx|upto)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakhs?|lac|l)\b', q_lower)
        if lakh_match:
            val = float(lakh_match.group(1)) * 100000.0
            budget_max = quantize_money(Decimal(str(val)))

        # 3. K / Thousand format (e.g. 80k, 120k, 35k, 50 thousand)
        elif re.search(r'(?:under|<|below|budget|within|max|around|approx|upto)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:k|thousand)\b', q_lower):
            k_match = re.search(r'(?:under|<|below|budget|within|max|around|approx|upto)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:k|thousand)\b', q_lower)
            val = float(k_match.group(1)) * 1000.0
            budget_max = quantize_money(Decimal(str(val)))

        # 4. Standard comma or raw numbers with currency prefix or suffix: ₹1,20,000 or Rs 120000 or 120000 INR
        elif re.search(r'(?:under|<|below|budget|within|max|upto)?\s*(?:₹|rs\.?|inr)\s*(\d{2,3}(?:,\d{2,3})+|\d{4,7})\b', q_lower):
            num_match = re.search(r'(?:under|<|below|budget|within|max|upto)?\s*(?:₹|rs\.?|inr)\s*(\d{2,3}(?:,\d{2,3})+|\d{4,7})\b', q_lower)
            raw = num_match.group(1).replace(",", "")
            budget_max = quantize_money(Decimal(raw))
        elif re.search(r'(\d{2,3}(?:,\d{2,3})+|\d{4,7})\s*(?:inr|rupees|rs\.?)\b', q_lower):
            num_match = re.search(r'(\d{2,3}(?:,\d{2,3})+|\d{4,7})\s*(?:inr|rupees|rs\.?)\b', q_lower)
            raw = num_match.group(1).replace(",", "")
            budget_max = quantize_money(Decimal(raw))
        elif re.search(r'(?:under|<|below|budget|within|max|upto)\s*(\d{2,3}(?:,\d{2,3})+|\d{4,7})\b', q_lower):
            num_match = re.search(r'(?:under|<|below|budget|within|max|upto)\s*(\d{2,3}(?:,\d{2,3})+|\d{4,7})\b', q_lower)
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
    ) -> Tuple[List[SpecificationConstraint], List[str]]:
        constraints: List[SpecificationConstraint] = []
        req_keywords: List[str] = []

        # 1. RAM Extraction (GB)
        ram_match = re.search(r'(\d+)\s*(?:gb|gigs?)\s*(?:ram|memory)?', q_lower)
        if ram_match:
            ram_val = int(ram_match.group(1))
            if ram_val in [4, 8, 12, 16, 18, 24, 32, 36, 48, 64, 128]:
                constraints.append(SpecificationConstraint(
                    key="ram_gb",
                    operator=ConstraintOperator.GTE,
                    target_value=ram_val,
                    is_hard_constraint=True,
                    unit="GB",
                    description=f"At least {ram_val}GB RAM"
                ))

        # 2. SSD / Storage Extraction (TB or GB)
        tb_match = re.search(r'(\d+)\s*tb\s*(?:ssd|storage|nvme|rom|hard drive)?', q_lower)
        gb_ssd_match = re.search(r'(\d{3,4})\s*(?:gb|gigs?)\s*(?:ssd|storage|nvme|rom)', q_lower)
        if tb_match:
            tb_val = int(tb_match.group(1)) * 1000
            constraints.append(SpecificationConstraint(
                key="ssd_gb",
                operator=ConstraintOperator.GTE,
                target_value=tb_val,
                is_hard_constraint=True,
                unit="GB",
                description=f"At least {tb_match.group(1)}TB SSD storage"
            ))
        elif gb_ssd_match:
            ssd_val = int(gb_ssd_match.group(1))
            constraints.append(SpecificationConstraint(
                key="ssd_gb",
                operator=ConstraintOperator.GTE,
                target_value=ssd_val,
                is_hard_constraint=True,
                unit="GB",
                description=f"At least {ssd_val}GB SSD storage"
            ))

        # 3. GPU Extraction (RTX / NVIDIA / Dedicated)
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
            elif "3060" in q_lower:
                gpu_kw = "3060"

            constraints.append(SpecificationConstraint(
                key="gpu",
                operator=ConstraintOperator.CONTAINS,
                target_value=gpu_kw,
                is_hard_constraint=True,
                description=f"NVIDIA GeForce {gpu_kw} GPU"
            ))
            req_keywords.append("RTX")
        elif any(w in q_lower for w in ["apple silicon", "m3 max", "m3 pro", "m4 pro", "m3", "m2"]):
            constraints.append(SpecificationConstraint(
                key="chip",
                operator=ConstraintOperator.CONTAINS,
                target_value="M3",
                is_hard_constraint=True,
                description="Apple Silicon Pro/Max Processor"
            ))

        # 4. Display Refresh Rate (Hz)
        hz_match = re.search(r'(\d{2,3})\s*hz', q_lower)
        if hz_match:
            hz_val = int(hz_match.group(1))
            constraints.append(SpecificationConstraint(
                key="refresh_rate_hz",
                operator=ConstraintOperator.GTE,
                target_value=hz_val,
                is_hard_constraint=False,
                unit="Hz",
                description=f"At least {hz_val}Hz Refresh Rate"
            ))

        # 5. Display Size (Inches)
        size_match = re.search(r'(\d{2}(?:\.\d)?)\s*(?:inch|\"|-inch|inches)', q_lower)
        if size_match:
            size_val = float(size_match.group(1))
            constraints.append(SpecificationConstraint(
                key="display_size_inches",
                operator=ConstraintOperator.GTE,
                target_value=size_val,
                is_hard_constraint=False,
                unit="inches",
                description=f"{size_val}-inch display format"
            ))

        # 6. Battery Endurance (Hours)
        batt_match = re.search(r'(\d+)\+?\s*(?:hours?|hrs?)\s*(?:battery|endurance|life)?', q_lower)
        if batt_match and ("battery" in q_lower or "life" in q_lower):
            batt_val = float(batt_match.group(1))
            constraints.append(SpecificationConstraint(
                key="battery_life_hours",
                operator=ConstraintOperator.GTE,
                target_value=batt_val,
                is_hard_constraint=False,
                unit="hours",
                description=f"Extended battery endurance (>= {batt_val} hours)"
            ))
        elif any(w in q_lower for w in ["good battery", "long battery", "all day battery", "battery life"]):
            constraints.append(SpecificationConstraint(
                key="battery_life_hours",
                operator=ConstraintOperator.GTE,
                target_value=8.0,
                is_hard_constraint=False,
                unit="hours",
                description="Extended battery endurance (>= 8 hours)"
            ))

        # 7. Power / Fast Charging (Watts)
        w_match = re.search(r'(\d{2,3})\s*w\b', q_lower)
        if w_match:
            w_val = int(w_match.group(1))
            constraints.append(SpecificationConstraint(
                key="wattage_w",
                operator=ConstraintOperator.GTE,
                target_value=w_val,
                is_hard_constraint=False,
                unit="W",
                description=f"{w_val}W Fast Charging / Power"
            ))

        # 8. Active Noise Cancellation (ANC)
        if any(w in q_lower for w in ["anc", "noise cancelling", "noise cancellation", "active noise"]):
            constraints.append(SpecificationConstraint(
                key="anc",
                operator=ConstraintOperator.EQ,
                target_value=True,
                is_hard_constraint=False,
                description="Active Noise Cancellation (ANC)"
            ))

        # Inherit previous constraints if refining without new ones
        if prev and not constraints:
            constraints = prev.spec_constraints
        if prev and not req_keywords:
            req_keywords = prev.required_keywords

        return constraints, req_keywords

    @classmethod
    def _extract_brands(cls, q_lower: str, prev: Optional[ShoppingIntent]) -> List[str]:
        brands = []
        known_brands = {
            "apple": "Apple",
            "asus": "ASUS",
            "rog": "ASUS",
            "acer": "Acer",
            "lenovo": "Lenovo",
            "dell": "Dell",
            "hp": "HP",
            "samsung": "Samsung",
            "sony": "Sony",
            "bose": "Bose",
            "lg": "LG",
            "logitech": "Logitech",
            "dyson": "Dyson",
            "delonghi": "DeLonghi"
        }
        for token, formal_name in known_brands.items():
            if re.search(rf'\b{token}\b', q_lower):
                brands.append(formal_name)

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
        if any(w in q_lower for w in ["cheapest", "lowest price", "lowest cost", "budget pick", "affordable", "cheap"]):
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
