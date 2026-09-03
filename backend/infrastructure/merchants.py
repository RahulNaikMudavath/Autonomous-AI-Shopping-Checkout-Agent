"""
Layer 4: Commerce Infrastructure - Merchants & Catalog
Simulates 4 independent merchants with inventory, dynamic pricing, and catalog search.
"""
from typing import List, Optional, Dict, Any
from backend.schemas import Product, ProductSpecs, Merchant

MERCHANTS: Dict[str, Merchant] = {
    "techhub_in": Merchant(
        id="techhub_in",
        name="TechHub India",
        domain="techhub.in",
        reputation_score=4.9,
        verified=True,
        express_delivery=True,
        supported_payment_methods=["UPI", "CREDIT_CARD", "ESCROW"],
        active_promotions=["AI_DEVELOPER_5OFF", "FREE_EXPRESS_SHIPPING"]
    ),
    "electrobazaar_in": Merchant(
        id="electrobazaar_in",
        name="ElectroBazaar",
        domain="electrobazaar.co.in",
        reputation_score=4.7,
        verified=True,
        express_delivery=True,
        supported_payment_methods=["UPI", "CREDIT_CARD", "DEBIT_CARD", "NET_BANKING"],
        active_promotions=["SUMMER_TECH_FEST"]
    ),
    "omnistore_in": Merchant(
        id="omnistore_in",
        name="OmniStore Online",
        domain="omnistore.in",
        reputation_score=4.6,
        verified=True,
        express_delivery=False,
        supported_payment_methods=["UPI", "CREDIT_CARD", "EMI"],
        active_promotions=["EXTRA_1YR_WARRANTY"]
    ),
    "prohardware_in": Merchant(
        id="prohardware_in",
        name="ProHardware Direct",
        domain="prohardware.com",
        reputation_score=4.8,
        verified=True,
        express_delivery=True,
        supported_payment_methods=["UPI", "CREDIT_CARD", "CORPORATE_INVOICE"],
        active_promotions=["ENTERPRISE_DEV_BUNDLE"]
    ),
}

# Catalog of realistic products across merchants
PRODUCT_CATALOG: List[Product] = [
    # --- Top AI/ML Contenders ---
    Product(
        id="prod_laptop_b_rog",
        merchant_id="techhub_in",
        merchant_name="TechHub India",
        title="ASUS ROG Strix G16 (2025) AI Workstation",
        category="laptops",
        brand="ASUS",
        price_inr=109999.0,
        original_price_inr=129999.0,
        currency="INR",
        rating=4.9,
        review_count=342,
        specs=ProductSpecs(
            gpu="NVIDIA GeForce RTX 4070 (140W TGP)",
            gpu_vram_gb=8,
            ram_gb=32,
            ssd_gb=1024,
            cpu="Intel Core i7-14650HX (16 Cores, 24 Threads)",
            battery_wh=90,
            battery_life_hours=8.5,
            display="16\" QHD+ 240Hz 100% DCI-P3 ROG Nebula",
            weight_kg=2.3
        ),
        in_stock=True,
        stock_quantity=18,
        delivery_days=2,
        shipping_fee_inr=0.0,
        image_url="https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=800&auto=format&fit=crop&q=80",
        return_window_days=14,
        warranty_years=2,
        description="Top-tier AI/ML dev machine. High-power 140W RTX 4070 with 90Wh massive battery for long untethered compute sessions."
    ),
    Product(
        id="prod_laptop_a_helios",
        merchant_id="electrobazaar_in",
        merchant_name="ElectroBazaar",
        title="Acer Predator Helios Neo 16 AI ML Edition",
        category="laptops",
        brand="Acer",
        price_inr=99999.0,
        original_price_inr=119999.0,
        currency="INR",
        rating=4.6,
        review_count=189,
        specs=ProductSpecs(
            gpu="NVIDIA GeForce RTX 4060 (140W TGP)",
            gpu_vram_gb=8,
            ram_gb=32,
            ssd_gb=1024,
            cpu="Intel Core i7-14700HX (20 Cores)",
            battery_wh=76,
            battery_life_hours=6.5,
            display="16\" WQXGA 165Hz IPS",
            weight_kg=2.6
        ),
        in_stock=True,
        stock_quantity=24,
        delivery_days=3,
        shipping_fee_inr=0.0,
        image_url="https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=800&auto=format&fit=crop&q=80",
        return_window_days=10,
        warranty_years=1,
        description="Exceptional sub-₹1L value. 32GB dual-channel RAM pre-installed, capable RTX 4060 for model fine-tuning."
    ),
    Product(
        id="prod_laptop_c_alienware",
        merchant_id="prohardware_in",
        merchant_name="ProHardware Direct",
        title="Dell G16 / Alienware ML Pro Max",
        category="laptops",
        brand="Dell",
        price_inr=117999.0,
        original_price_inr=134999.0,
        currency="INR",
        rating=4.8,
        review_count=98,
        specs=ProductSpecs(
            gpu="NVIDIA GeForce RTX 4070 (140W TGP)",
            gpu_vram_gb=8,
            ram_gb=64,
            ssd_gb=2048,
            cpu="Intel Core i9-13900HX (24 Cores)",
            battery_wh=86,
            battery_life_hours=7.0,
            display="16\" QHD+ 240Hz G-SYNC",
            weight_kg=2.7
        ),
        in_stock=True,
        stock_quantity=8,
        delivery_days=2,
        shipping_fee_inr=0.0,
        image_url="https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800&auto=format&fit=crop&q=80",
        return_window_days=15,
        warranty_years=2,
        description="Massive 64GB RAM & 2TB NVMe SSD configuration for large local LLM quantization and heavy datasets."
    ),
    Product(
        id="prod_laptop_lenovo_legion",
        merchant_id="omnistore_in",
        merchant_name="OmniStore Online",
        title="Lenovo Legion Pro 5i Gen 9",
        category="laptops",
        brand="Lenovo",
        price_inr=114999.0,
        original_price_inr=132000.0,
        currency="INR",
        rating=4.7,
        review_count=215,
        specs=ProductSpecs(
            gpu="NVIDIA GeForce RTX 4070 (140W TGP)",
            gpu_vram_gb=8,
            ram_gb=32,
            ssd_gb=1024,
            cpu="AMD Ryzen 7 8845HS with Ryzen AI NPU",
            battery_wh=80,
            battery_life_hours=7.8,
            display="16\" WQXGA 165Hz 500 nits",
            weight_kg=2.4
        ),
        in_stock=True,
        stock_quantity=12,
        delivery_days=4,
        shipping_fee_inr=499.0,
        image_url="https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=800&auto=format&fit=crop&q=80",
        return_window_days=14,
        warranty_years=3,
        description="Lenovo AI Engine+ powered by LA1 AI chip. Robust thermal dissipation ColdFront 5.0."
    ),
    Product(
        id="prod_laptop_macbook_pro_m3",
        merchant_id="techhub_in",
        merchant_name="TechHub India",
        title="Apple MacBook Pro 14 (M3 Pro, 18GB Unified, 512GB)",
        category="laptops",
        brand="Apple",
        price_inr=189900.0,
        original_price_inr=199900.0,
        currency="INR",
        rating=4.9,
        review_count=520,
        specs=ProductSpecs(
            gpu="Apple 14-core GPU (Unified)",
            gpu_vram_gb=18,
            ram_gb=18,
            ssd_gb=512,
            cpu="Apple M3 Pro (11-core CPU)",
            battery_wh=70,
            battery_life_hours=17.0,
            display="14.2\" Liquid Retina XDR 120Hz ProMotion",
            weight_kg=1.6
        ),
        in_stock=True,
        stock_quantity=10,
        delivery_days=1,
        shipping_fee_inr=0.0,
        image_url="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&auto=format&fit=crop&q=80",
        return_window_days=14,
        warranty_years=1,
        description="Industry-leading battery life & unified memory architecture for CoreML."
    ),
    Product(
        id="prod_laptop_asus_tuf_budget",
        merchant_id="electrobazaar_in",
        merchant_name="ElectroBazaar",
        title="ASUS TUF Gaming A15 AI Dev Starter",
        category="laptops",
        brand="ASUS",
        price_inr=74999.0,
        original_price_inr=89999.0,
        currency="INR",
        rating=4.5,
        review_count=410,
        specs=ProductSpecs(
            gpu="NVIDIA GeForce RTX 4050 (105W TGP)",
            gpu_vram_gb=6,
            ram_gb=16,
            ssd_gb=512,
            cpu="AMD Ryzen 7 7735HS",
            battery_wh=90,
            battery_life_hours=9.0,
            display="15.6\" FHD 144Hz 100% sRGB",
            weight_kg=2.2
        ),
        in_stock=True,
        stock_quantity=30,
        delivery_days=2,
        shipping_fee_inr=0.0,
        image_url="https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=800&auto=format&fit=crop&q=80",
        return_window_days=10,
        warranty_years=1,
        description="Ultra-budget entry machine for students starting deep learning and computer vision."
    )
]

def get_all_merchants() -> List[Merchant]:
    return list(MERCHANTS.values())

def get_merchant_by_id(merchant_id: str) -> Optional[Merchant]:
    return MERCHANTS.get(merchant_id)

def search_merchant_catalog(
    query: Optional[str] = None,
    merchant_id: Optional[str] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_ram: Optional[int] = None,
    gpu_filter: Optional[str] = None
) -> List[Product]:
    results = PRODUCT_CATALOG
    
    if merchant_id:
        results = [p for p in results if p.merchant_id == merchant_id]
        
    if category:
        results = [p for p in results if p.category.lower() == category.lower()]
        
    if max_price is not None:
        results = [p for p in results if p.price_inr <= max_price]
        
    if min_ram is not None:
        results = [p for p in results if p.specs.ram_gb >= min_ram]
        
    if gpu_filter:
        results = [p for p in results if gpu_filter.lower() in p.specs.gpu.lower()]
        
    if query:
        q_lower = query.lower()
        # Token match
        terms = [t for t in q_lower.split() if len(t) > 2]
        if terms:
            def matches(p: Product) -> bool:
                combined = f"{p.title} {p.brand} {p.description} {p.specs.gpu} {p.specs.cpu}".lower()
                return any(term in combined for term in terms)
            results = [p for p in results if matches(p)]
            
    return results
