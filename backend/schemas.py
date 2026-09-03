"""
AgentCart Pydantic Schemas
Defines core data models across all 5 architectural layers.
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

# --- Layer 4: Product & Hardware Specs ---
class ProductSpecs(BaseModel):
    gpu: str = Field(..., description="GPU model, e.g. NVIDIA RTX 4060, RTX 4070")
    gpu_vram_gb: int = Field(default=8, description="GPU VRAM in GB")
    ram_gb: int = Field(..., description="RAM size in GB")
    ssd_gb: int = Field(..., description="SSD storage in GB")
    cpu: str = Field(..., description="CPU model, e.g. Intel Core i7-14700HX, AMD Ryzen 7 8845HS")
    battery_wh: int = Field(default=75, description="Battery capacity in Watt-hours")
    battery_life_hours: float = Field(default=7.5, description="Estimated battery life in hours")
    display: str = Field(default="15.6\" QHD 165Hz", description="Display specs")
    weight_kg: float = Field(default=2.1, description="Weight in kg")

class Product(BaseModel):
    id: str
    merchant_id: str
    merchant_name: str
    title: str
    category: str = "laptops"
    brand: str
    price_inr: float
    original_price_inr: float
    currency: str = "INR"
    rating: float = 4.5
    review_count: int = 120
    specs: ProductSpecs
    in_stock: bool = True
    stock_quantity: int = 15
    delivery_days: int = 2
    shipping_fee_inr: float = 0.0
    image_url: str = ""
    return_window_days: int = 14
    warranty_years: int = 1
    description: str = ""
    value_score: Optional[float] = None
    value_breakdown: Optional[Dict[str, Any]] = None

class Merchant(BaseModel):
    id: str
    name: str
    domain: str
    reputation_score: float = 4.8
    verified: bool = True
    express_delivery: bool = True
    supported_payment_methods: List[str] = ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NET_BANKING", "ESCROW"]
    active_promotions: List[str] = []

# --- Layer 2: Agent Requirements & Intelligence ---
class UserRequirements(BaseModel):
    raw_query: str
    budget_max_inr: Optional[float] = None
    min_ram_gb: Optional[int] = None
    gpu_brand_preference: Optional[str] = None # e.g. "NVIDIA", "AMD", "Apple"
    min_gpu_vram_gb: Optional[int] = None
    min_ssd_gb: Optional[int] = None
    battery_priority: Literal["low", "medium", "high"] = "medium"
    objective: Literal["best_value", "highest_performance", "lowest_price", "balanced"] = "best_value"
    category: str = "laptops"
    target_use_case: Optional[str] = "AI/ML development"

class TraceStep(BaseModel):
    step_id: str
    title: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: Literal["running", "completed", "warning", "failed"] = "completed"
    summary: str
    details: Optional[Dict[str, Any]] = None
    execution_time_ms: int = 45

class RecommendationResult(BaseModel):
    top_recommendation: Optional[Product] = None
    explanation: str
    trade_off_analysis: str
    comparison_table: List[Product] = []
    requirements_extracted: UserRequirements
    trace: List[TraceStep] = []
    policy_status: Dict[str, Any] = {}

# --- Layer 5: Trust & Safety Policies ---
class SpendingPolicy(BaseModel):
    max_budget_limit_inr: float = 150000.0
    single_item_approval_threshold_inr: float = 50000.0  # Above this, require human confirmation
    daily_velocity_limit_inr: float = 200000.0
    allowed_categories: List[str] = ["laptops", "gpus", "monitors", "electronics", "accessories"]
    blocked_merchants: List[str] = []
    trusted_merchants_only: bool = True
    auto_approve_under_threshold: bool = True
    prompt_injection_defense_enabled: bool = True

class PolicyCheckResult(BaseModel):
    passed: bool
    requires_human_approval: bool
    policy_violations: List[str] = []
    warning_notes: List[str] = []
    spending_ceiling_ok: bool = True
    single_item_threshold_triggered: bool = False
    merchant_trusted: bool = True

class PromptInjectionScanResult(BaseModel):
    is_malicious: bool
    threat_level: Literal["safe", "low", "medium", "critical"] = "safe"
    detected_patterns: List[str] = []
    sanitized_input: str

class AuditBlock(BaseModel):
    block_index: int
    timestamp: str
    action_type: str  # "SEARCH", "EVALUATE", "POLICY_CHECK", "CART_ADD", "CHECKOUT_AUTH", "ORDER_PLACED", "INJECTION_BLOCKED"
    actor: str  # "AGENT", "USER", "MERCHANT_GATEWAY"
    payload_summary: str
    previous_hash: str
    current_hash: str
    policy_verified: bool = True

# --- Layer 4: Cart & Orders ---
class CartItem(BaseModel):
    product: Product
    quantity: int = 1
    selected_merchant_id: str
    unit_price_inr: float
    total_price_inr: float

class Cart(BaseModel):
    cart_id: str
    items: List[CartItem] = []
    subtotal_inr: float = 0.0
    shipping_total_inr: float = 0.0
    tax_total_inr: float = 0.0
    discount_total_inr: float = 0.0
    grand_total_inr: float = 0.0
    currency: str = "INR"

class CheckoutQuote(BaseModel):
    quote_id: str
    cart_id: str
    product_title: str
    merchant_name: str
    amount_inr: float
    breakdown: Dict[str, float]
    tokenized_payment_methods: List[str] = ["UPI_TOKEN_4829", "SAVED_CARD_VISA_8821"]
    policy_check: PolicyCheckResult
    expires_at: str

class Order(BaseModel):
    order_id: str
    merchant_id: str
    merchant_name: str
    product: Product
    amount_inr: float
    payment_method: str = "UPI (Tokenized)"
    payment_status: Literal["PENDING", "AUTHORIZED", "SETTLED", "REFUNDED"] = "AUTHORIZED"
    order_status: Literal["PENDING_APPROVAL", "CONFIRMED", "PROCESSING", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED", "RETURN_REQUESTED", "RETURNED"] = "CONFIRMED"
    tracking_id: str
    estimated_delivery: str
    created_at: str
    updated_at: str
    shipping_address: str = "Rahul N., Flat 402, HighTech Tech Park, Bangalore 560100"
    audit_block_hash: str = ""
    return_reason: Optional[str] = None

# --- Layer 3: UCP & ACP Protocols & MCP ---
class UCPCatalogSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    specs_filter: Optional[Dict[str, Any]] = None

class UCPCatalogResponse(BaseModel):
    protocol_version: str = "UCP/1.0"
    total_count: int
    merchants_polled: List[str]
    products: List[Product] = []

class UCPHeader(BaseModel):
    version: str = "1.0"
    sender: str = "AgentCart-Core"
    recipient: str = "MerchantGateway"
    action: str
    message_id: str
    timestamp: str

class UCPPayload(BaseModel):
    data: Dict[str, Any]

class UCPEnvelope(BaseModel):
    header: UCPHeader
    payload: UCPPayload

class MCPToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class MCPToolCallResponse(BaseModel):
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
