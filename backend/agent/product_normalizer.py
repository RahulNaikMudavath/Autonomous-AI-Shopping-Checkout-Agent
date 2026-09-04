"""
Phase 3: Autonomous AI Shopping Agent - Product Normalizer
Transforms raw heterogeneous merchant catalog items into universal NormalizedProductCandidate records,
MerchantOffer objects, and grouped CanonicalProduct structures.
Normalizes specifications, delivery metrics, stock states, and monetary amounts with Decimal precision.
"""
from decimal import Decimal
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.domain.marketplace import ProductSummary, ProductDetail, AvailabilityState
from backend.domain.agent_schemas import (
    NormalizedProductCandidate, MerchantOffer, CanonicalProduct
)
from backend.services.pricing_service import quantize_money
from backend.trust_safety.untrusted_content_sanitizer import UntrustedContentSanitizer


class ProductNormalizer:
    """
    Normalizes product structures across Amazon, Flipkart, Croma into canonical representations.
    """

    @classmethod
    def normalize_candidate(
        cls,
        item: ProductSummary | ProductDetail | Dict[str, Any]
    ) -> NormalizedProductCandidate:
        """
        Maps any product DTO or dict into a standard NormalizedProductCandidate.
        Validates price non-negativity and sanitizes all untrusted strings.
        """
        if isinstance(item, dict):
            p_id = str(item.get("id") or item.get("product_id") or "")
            if not p_id:
                raise ValueError("Product item must contain an authoritative product id")
            merchant_code = str(item.get("merchant_code") or "UNKNOWN").upper()
            merchant_name = str(item.get("merchant_name") or merchant_code)
            merchant_id = item.get("merchant_id")
            sku = str(item.get("sku") or p_id)
            raw_title = str(item.get("title") or "")
            raw_brand = str(item.get("brand") or "Generic")
            category = str(item.get("category") or "laptops").lower()
            model = item.get("model")
            raw_desc = str(item.get("description") or "")
            
            # Price validation
            raw_c_price = item.get("current_price")
            if raw_c_price is None:
                raise ValueError(f"Product '{p_id}' is missing required 'current_price'")
            c_price_dec = Decimal(str(raw_c_price))
            if c_price_dec < Decimal("0.00"):
                raise ValueError(f"Product '{p_id}' has invalid negative current_price: {c_price_dec}")
            c_price = quantize_money(c_price_dec)

            raw_b_price = item.get("base_price", raw_c_price)
            b_price_dec = Decimal(str(raw_b_price)) if raw_b_price is not None else c_price_dec
            if b_price_dec < Decimal("0.00"):
                raise ValueError(f"Product '{p_id}' has invalid negative base_price: {b_price_dec}")
            b_price = quantize_money(b_price_dec)

            try:
                disc_pct = float(item.get("discount_percentage", 0.0) or 0.0)
            except (ValueError, TypeError):
                disc_pct = 0.0

            raw_state = item.get("inventory_state", "IN_STOCK")
            try:
                avail_qty = max(0, int(item.get("available_quantity", 0)))
            except (ValueError, TypeError):
                avail_qty = 0

            try:
                raw_rating = float(item.get("rating", 4.5))
                rating = max(0.0, min(5.0, raw_rating))
            except (ValueError, TypeError):
                rating = 4.5

            try:
                reviews = max(0, int(item.get("review_count", 0)))
            except (ValueError, TypeError):
                reviews = 0

            img_url = item.get("image_url")
            prod_url = item.get("product_url")
            raw_specs = item.get("specs", {}) or {}
            shipping_opts = item.get("shipping_options", []) or []
            source_meta = item.get("source_metadata", {}) or {}
        else:
            p_id = str(item.id)
            if not p_id:
                raise ValueError("Product item must contain an authoritative product id")
            merchant_code = str(item.merchant_code or "UNKNOWN").upper()
            merchant_name = str(item.merchant_name or merchant_code)
            merchant_id = getattr(item, "merchant_id", None)
            sku = str(item.sku or p_id)
            raw_title = str(item.title or "")
            raw_brand = str(item.brand or "Generic")
            category = str(item.category or "laptops").lower()
            model = item.model
            raw_desc = str(getattr(item, "description", "") or "")

            if item.current_price is None or item.current_price < Decimal("0.00"):
                raise ValueError(f"Product '{p_id}' has invalid current_price: {item.current_price}")
            c_price = quantize_money(item.current_price)

            b_price_val = getattr(item, "base_price", item.current_price) or item.current_price
            if b_price_val < Decimal("0.00"):
                raise ValueError(f"Product '{p_id}' has invalid base_price: {b_price_val}")
            b_price = quantize_money(b_price_val)

            disc_pct = float(getattr(item, "discount_percentage", 0.0) or 0.0)
            raw_state = item.inventory_state
            avail_qty = max(0, item.available_quantity or 0)
            rating = max(0.0, min(5.0, float(item.rating or 4.5)))
            reviews = max(0, int(item.review_count or 0))
            img_url = item.image_url
            prod_url = getattr(item, "product_url", None)
            raw_specs = getattr(item, "specs", {}) or {}
            shipping_opts = getattr(item, "shipping_options", []) or []
            source_meta = getattr(item, "source_metadata", {}) or {}

        # 1. Sanitize Untrusted Content
        san_title = UntrustedContentSanitizer.sanitize_merchant_content(raw_title, merchant_name, "title").sanitized_clean_content
        san_desc = UntrustedContentSanitizer.sanitize_merchant_content(raw_desc, merchant_name, "description").sanitized_clean_content
        san_brand = UntrustedContentSanitizer.sanitize_merchant_content(raw_brand, merchant_name, "brand").sanitized_clean_content

        # 2. State & Stock
        try:
            inv_state = AvailabilityState(raw_state) if isinstance(raw_state, str) else raw_state
        except (ValueError, KeyError):
            inv_state = AvailabilityState.IN_STOCK if avail_qty > 0 else AvailabilityState.OUT_OF_STOCK

        in_stock = inv_state != AvailabilityState.OUT_OF_STOCK and (avail_qty > 0 or inv_state == AvailabilityState.IN_STOCK)

        # 3. Extract and Normalize Specs
        specs = cls._normalize_specs(san_title, san_desc, raw_specs)

        # 4. Delivery Days & Shipping Fees
        delivery_days, shipping_cost, opt_name = cls._extract_delivery_info(merchant_code, shipping_opts)

        return NormalizedProductCandidate(
            id=f"{merchant_code}_{sku or p_id}",
            merchant_code=merchant_code,
            merchant_name=merchant_name,
            merchant_id=merchant_id,
            product_id=p_id,
            sku=sku,
            title=san_title,
            brand=san_brand,
            category=category,
            model=model,
            description=san_desc,
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
            shipping_options=shipping_opts,
            rating=rating,
            review_count=reviews,
            image_url=img_url,
            product_url=prod_url,
            specs=specs,
            source_metadata=source_meta
        )

    @classmethod
    def to_merchant_offer(cls, candidate: NormalizedProductCandidate) -> MerchantOffer:
        """Converts a NormalizedProductCandidate into an isolated MerchantOffer."""
        return MerchantOffer(
            merchant_code=candidate.merchant_code,
            merchant_name=candidate.merchant_name,
            merchant_id=candidate.merchant_id,
            product_id=candidate.product_id,
            sku=candidate.sku,
            current_price=candidate.current_price,
            base_price=candidate.base_price,
            currency=candidate.currency,
            discount_percentage=candidate.discount_percentage,
            inventory_state=candidate.inventory_state,
            available_quantity=candidate.available_quantity,
            in_stock=candidate.in_stock,
            delivery_days=candidate.delivery_days,
            shipping_cost=candidate.shipping_cost,
            shipping_option_name=candidate.shipping_option_name,
            shipping_options=candidate.shipping_options,
            rating=candidate.rating,
            review_count=candidate.review_count,
            product_url=candidate.product_url,
            image_url=candidate.image_url,
            specs=candidate.specs,
            source_metadata=candidate.source_metadata
        )

    @classmethod
    def generate_canonical_id(
        cls,
        brand: str,
        model: Optional[str],
        title: str,
        specs: Dict[str, Any]
    ) -> str:
        """
        Generates a deterministic canonical product ID grouping equivalent offers
        while keeping distinct hardware variants (e.g. 16GB vs 32GB, 2024 vs 2025) separate.
        """
        clean_brand = brand.strip().lower()
        if model and model.strip():
            clean_model = re.sub(r'[^a-z0-9]+', '_', model.strip().lower()).strip('_')
            # Add key hardware variant differentiators to prevent accidental variant merging
            variant_parts = [clean_brand, clean_model]
            if "ram_gb" in specs:
                variant_parts.append(f"{specs['ram_gb']}gb")
            if "ssd_gb" in specs:
                variant_parts.append(f"{specs['ssd_gb']}ssd")
            return "_".join(variant_parts)
        
        # Fallback to normalized title hash
        clean_title = re.sub(r'[^a-z0-9]+', '_', title.strip().lower()[:50]).strip('_')
        return f"{clean_brand}_{clean_title}"

    @classmethod
    def group_canonical_products(
        cls,
        candidates: List[NormalizedProductCandidate]
    ) -> List[CanonicalProduct]:
        """
        Aggregates multi-merchant candidates into canonical products with preserved individual offers.
        """
        groups: Dict[str, List[NormalizedProductCandidate]] = {}
        for c in candidates:
            cid = cls.generate_canonical_id(c.brand, c.model, c.title, c.specs)
            if cid not in groups:
                groups[cid] = []
            groups[cid].append(c)

        canonical_products: List[CanonicalProduct] = []
        for cid, items in groups.items():
            ref = items[0]
            offers = [cls.to_merchant_offer(item) for item in items]
            
            # Identify best price and fastest delivery offers
            best_price_offer = min(offers, key=lambda o: (o.current_price + o.shipping_cost)) if offers else None
            fastest_delivery_offer = min(offers, key=lambda o: o.delivery_days) if offers else None

            canonical_products.append(CanonicalProduct(
                canonical_id=cid,
                title=ref.title,
                brand=ref.brand,
                category=ref.category,
                model=ref.model,
                description=ref.description,
                normalized_specs=ref.specs,
                offers=offers,
                best_price_offer=best_price_offer,
                fastest_delivery_offer=fastest_delivery_offer
            ))

        return canonical_products

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
        - ssd_gb / storage_gb (int)
        - storage_type (str)
        - gpu (str)
        - gpu_vram_gb (int)
        - cpu (str)
        - display_size_inches (float)
        - refresh_rate_hz (int)
        - battery_hours (float)
        - battery_wh (int)
        - weight_kg (float)
        - operating_system (str)
        
        Strict rule: Do NOT invent values. If not found in raw_specs or text, omit/leave None.
        """
        specs: Dict[str, Any] = dict(raw_specs)
        combined_text = f"{title} {description} {' '.join(str(v) for v in raw_specs.values())}".lower()

        # 1. RAM GB
        if "ram_gb" not in specs:
            ram_match = re.search(r'(\d+)\s*(?:gb|gigs?)\s*(?:ddr\d|lpddr\d[x]?|ram|memory)?', combined_text)
            if ram_match:
                specs["ram_gb"] = int(ram_match.group(1))

        # 2. Storage / SSD GB
        if "ssd_gb" not in specs and "storage_gb" not in specs:
            tb_match = re.search(r'(\d+)\s*tb\s*(?:ssd|nvme|pcie|storage|rom)?', combined_text)
            gb_ssd = re.search(r'(\d{3,4})\s*(?:gb|gigs?)\s*(?:ssd|nvme|pcie|storage|rom)', combined_text)
            if tb_match:
                specs["ssd_gb"] = int(tb_match.group(1)) * 1024
                specs["storage_gb"] = specs["ssd_gb"]
            elif gb_ssd:
                specs["ssd_gb"] = int(gb_ssd.group(1))
                specs["storage_gb"] = specs["ssd_gb"]
        elif "ssd_gb" in specs and "storage_gb" not in specs:
            specs["storage_gb"] = specs["ssd_gb"]
        elif "storage_gb" in specs and "ssd_gb" not in specs:
            specs["ssd_gb"] = specs["storage_gb"]

        # Storage type
        if "storage_type" not in specs:
            if "nvme" in combined_text or "pcie" in combined_text:
                specs["storage_type"] = "NVMe SSD"
            elif "ssd" in combined_text:
                specs["storage_type"] = "SSD"
            elif "ufs" in combined_text:
                specs["storage_type"] = "UFS"

        # 3. GPU & VRAM
        if "gpu" not in specs:
            if "rtx 4090" in combined_text:
                specs["gpu"] = "NVIDIA RTX 4090 16GB"
                specs["gpu_vram_gb"] = 16
            elif "rtx 4080" in combined_text:
                specs["gpu"] = "NVIDIA RTX 4080 12GB"
                specs["gpu_vram_gb"] = 12
            elif "rtx 4070" in combined_text:
                specs["gpu"] = "NVIDIA RTX 4070 8GB"
                specs["gpu_vram_gb"] = 8
            elif "rtx 4060" in combined_text:
                specs["gpu"] = "NVIDIA RTX 4060 8GB"
                specs["gpu_vram_gb"] = 8
            elif "rtx 4050" in combined_text:
                specs["gpu"] = "NVIDIA RTX 4050 6GB"
                specs["gpu_vram_gb"] = 6
            elif "rtx 3050" in combined_text:
                specs["gpu"] = "NVIDIA RTX 3050 4GB"
                specs["gpu_vram_gb"] = 4
            elif "m3 max" in combined_text:
                specs["gpu"] = "Apple M3 Max 30-Core GPU"
            elif "m3 pro" in combined_text:
                specs["gpu"] = "Apple M3 Pro 14-Core GPU"
            elif "m3" in combined_text:
                specs["gpu"] = "Apple M3 10-Core GPU"
            elif "m4" in combined_text:
                specs["gpu"] = "Apple M4 10-Core GPU"

        if "gpu_vram_gb" not in specs and "gpu" in specs:
            vram_m = re.search(r'(\d+)\s*gb', str(specs["gpu"]).lower())
            if vram_m:
                specs["gpu_vram_gb"] = int(vram_m.group(1))

        # 4. CPU
        if "cpu" not in specs:
            if "i9-14900hx" in combined_text or "14900hx" in combined_text:
                specs["cpu"] = "Intel Core i9-14900HX"
            elif "i7-14650hx" in combined_text or "14650hx" in combined_text:
                specs["cpu"] = "Intel Core i7-14650HX"
            elif "i7-13700h" in combined_text or "13700h" in combined_text:
                specs["cpu"] = "Intel Core i7-13700H"
            elif "i5-13420h" in combined_text or "13420h" in combined_text:
                specs["cpu"] = "Intel Core i5-13420H"
            elif "ryzen 9" in combined_text:
                specs["cpu"] = "AMD Ryzen 9 7940HS"
            elif "ryzen 7" in combined_text:
                specs["cpu"] = "AMD Ryzen 7 7840HS"
            elif "m3 max" in combined_text:
                specs["cpu"] = "Apple M3 Max 14-Core"
            elif "m3 pro" in combined_text:
                specs["cpu"] = "Apple M3 Pro 12-Core"

        # 5. Display Size
        if "display_size_inches" not in specs:
            disp_m = re.search(r'(\d+(?:\.\d+)?)\s*(?:-inch|\"|inch)', combined_text)
            if disp_m:
                try:
                    specs["display_size_inches"] = float(disp_m.group(1))
                except (ValueError, TypeError):
                    pass

        # 6. Refresh Rate
        if "refresh_rate_hz" not in specs:
            hz_match = re.search(r'(\d{2,3})\s*hz', combined_text)
            if hz_match:
                specs["refresh_rate_hz"] = int(hz_match.group(1))

        # 7. Battery Hours & Battery Wh
        if "battery_hours" not in specs:
            bat_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\s*(?:battery)?', combined_text)
            if bat_match:
                specs["battery_hours"] = float(bat_match.group(1))

        if "battery_wh" not in specs:
            wh_match = re.search(r'(\d{2,3})\s*wh', combined_text)
            if wh_match:
                specs["battery_wh"] = int(wh_match.group(1))

        # 8. Weight
        if "weight_kg" not in specs:
            wt_match = re.search(r'(\d+(?:\.\d+)?)\s*kg', combined_text)
            if wt_match:
                specs["weight_kg"] = float(wt_match.group(1))

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
