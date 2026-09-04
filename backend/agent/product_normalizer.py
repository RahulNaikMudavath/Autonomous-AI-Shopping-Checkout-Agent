"""
Phase 3: Autonomous AI Shopping Agent - Product Normalizer
Transforms raw heterogeneous merchant catalog items into universal NormalizedProductCandidate records.
Normalizes specifications, delivery metrics, stock states, and monetary amounts.
"""
from decimal import Decimal
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.domain.marketplace import ProductSummary, ProductDetail, AvailabilityState
from backend.domain.agent_schemas import NormalizedProductCandidate
from backend.services.pricing_service import quantize_money


class ProductNormalizer:
    """
    Normalizes product structures across Amazon, Flipkart, Croma.
    """

    @classmethod
    def normalize_candidate(
        cls,
        item: ProductSummary | ProductDetail | Dict[str, Any]
    ) -> NormalizedProductCandidate:
        """
        Maps any product DTO into a standard NormalizedProductCandidate.
        """
        if isinstance(item, dict):
            p_id = item.get("id", "")
            merchant_code = item.get("merchant_code", "UNKNOWN")
            merchant_name = item.get("merchant_name", merchant_code)
            sku = item.get("sku", "")
            title = item.get("title", "")
            brand = item.get("brand", "")
            category = item.get("category", "laptops")
            model = item.get("model")
            description = item.get("description", "")
            c_price = quantize_money(Decimal(str(item.get("current_price", "0.00"))))
            b_price = quantize_money(Decimal(str(item.get("base_price", item.get("current_price", "0.00")))))
            disc_pct = float(item.get("discount_percentage", 0.0))
            raw_state = item.get("inventory_state", "IN_STOCK")
            avail_qty = int(item.get("available_quantity", 0))
            rating = float(item.get("rating", 4.5))
            reviews = int(item.get("review_count", 0))
            img_url = item.get("image_url")
            raw_specs = item.get("specs", {})
            shipping_opts = item.get("shipping_options", [])
        else:
            p_id = item.id
            merchant_code = item.merchant_code or "UNKNOWN"
            merchant_name = item.merchant_name or merchant_code
            sku = item.sku
            title = item.title
            brand = item.brand
            category = item.category
            model = item.model
            description = getattr(item, "description", "")
            c_price = quantize_money(item.current_price)
            b_price = quantize_money(item.base_price)
            disc_pct = getattr(item, "discount_percentage", 0.0) or 0.0
            raw_state = item.inventory_state
            avail_qty = item.available_quantity
            rating = item.rating
            reviews = item.review_count
            img_url = item.image_url
            raw_specs = getattr(item, "specs", {}) or {}
            shipping_opts = getattr(item, "shipping_options", []) or []

        # 1. State & Stock
        inv_state = AvailabilityState(raw_state) if isinstance(raw_state, str) else raw_state
        in_stock = inv_state != AvailabilityState.OUT_OF_STOCK and (avail_qty > 0 or inv_state == AvailabilityState.IN_STOCK)

        # 2. Extract and Normalize Specs
        specs = cls._normalize_specs(title, description, raw_specs)

        # 3. Delivery Days & Shipping Fees
        delivery_days, shipping_cost, opt_name = cls._extract_delivery_info(merchant_code, shipping_opts)

        return NormalizedProductCandidate(
            id=f"{merchant_code}_{sku or p_id}",
            merchant_code=merchant_code,
            merchant_name=merchant_name,
            product_id=p_id,
            sku=sku,
            title=title,
            brand=brand,
            category=category,
            model=model,
            description=description,
            current_price=c_price,
            base_price=b_price,
            discount_percentage=disc_pct,
            currency="INR",
            inventory_state=inv_state,
            available_quantity=avail_qty,
            in_stock=in_stock,
            delivery_days=delivery_days,
            shipping_cost=shipping_cost,
            shipping_option_name=opt_name,
            rating=rating,
            review_count=reviews,
            image_url=img_url,
            specs=specs
        )

    @classmethod
    def _normalize_specs(
        cls,
        title: str,
        description: str,
        raw_specs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Harmonizes specifications into standardized numeric/text keys:
        - ram_gb (int)
        - ssd_gb (int)
        - gpu (str)
        - cpu (str)
        - battery_hours (float)
        - battery_wh (int)
        - refresh_rate_hz (int)
        - weight_kg (float)
        """
        specs = dict(raw_specs)
        combined_text = f"{title} {description} {' '.join(str(v) for v in raw_specs.values())}".lower()

        # 1. RAM GB
        if "ram_gb" not in specs:
            ram_match = re.search(r'(\d+)\s*(?:gb|gigs?)\s*(?:ram|memory)?', combined_text)
            if ram_match:
                specs["ram_gb"] = int(ram_match.group(1))

        # 2. SSD GB
        if "ssd_gb" not in specs:
            tb_match = re.search(r'(\d+)\s*tb\s*(?:ssd|storage|nvme|rom)?', combined_text)
            gb_ssd = re.search(r'(\d{3,4})\s*(?:gb|gigs?)\s*(?:ssd|storage|nvme|rom)', combined_text)
            if tb_match:
                specs["ssd_gb"] = int(tb_match.group(1)) * 1024
            elif gb_ssd:
                specs["ssd_gb"] = int(gb_ssd.group(1))

        # 3. GPU
        if "gpu" not in specs:
            if "rtx 4090" in combined_text:
                specs["gpu"] = "NVIDIA RTX 4090 16GB"
            elif "rtx 4080" in combined_text:
                specs["gpu"] = "NVIDIA RTX 4080 12GB"
            elif "rtx 4070" in combined_text:
                specs["gpu"] = "NVIDIA RTX 4070 8GB"
            elif "rtx 4060" in combined_text:
                specs["gpu"] = "NVIDIA RTX 4060 8GB"
            elif "rtx 4050" in combined_text:
                specs["gpu"] = "NVIDIA RTX 4050 6GB"
            elif "m3 max" in combined_text:
                specs["gpu"] = "Apple M3 Max 30-Core GPU"
            elif "m3 pro" in combined_text:
                specs["gpu"] = "Apple M3 Pro 14-Core GPU"
            elif "m4" in combined_text:
                specs["gpu"] = "Apple M4 10-Core GPU"

        # 4. Refresh Rate
        if "refresh_rate_hz" not in specs:
            hz_match = re.search(r'(\d{2,3})\s*hz', combined_text)
            if hz_match:
                specs["refresh_rate_hz"] = int(hz_match.group(1))

        # 5. Battery Hours
        if "battery_hours" not in specs:
            bat_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\s*(?:battery)?', combined_text)
            if bat_match:
                specs["battery_hours"] = float(bat_match.group(1))
            else:
                specs["battery_hours"] = 8.0  # default estimate

        return specs

    @classmethod
    def _extract_delivery_info(
        cls,
        merchant_code: str,
        shipping_opts: List[Dict[str, Any]]
    ) -> Tuple[int, Decimal, str]:
        """
        Determines realistic delivery speed and standard shipping fee.
        """
        if shipping_opts:
            # Sort by fastest delivery days
            sorted_opts = sorted(shipping_opts, key=lambda o: o.get("estimated_days", 3))
            fastest = sorted_opts[0]
            days = int(fastest.get("estimated_days", 3))
            cost = quantize_money(Decimal(str(fastest.get("cost", "0.00"))))
            name = fastest.get("name", "Standard Delivery")
            return days, cost, name

        # Merchant Defaults
        if merchant_code == "AMAZON":
            return 1, Decimal("99.00"), "Amazon Prime Express"
        elif merchant_code == "FLIPKART":
            return 2, Decimal("79.00"), "Flipkart SuperFast"
        elif merchant_code == "CROMA":
            return 1, Decimal("149.00"), "Croma 24-Hour Express"
        return 3, Decimal("0.00"), "Standard Delivery"
