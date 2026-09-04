"""
Phase 3: Autonomous AI Shopping Agent Schemas & DTOs
Defines structured schemas for:
- Specification constraints (hard vs soft)
- Structured Shopping Intent with unit normalization
- Normalized Product Candidates across merchants
- Constraint evaluation audit results
- Multi-Criteria Decision Analysis (MCDA) score breakdowns
- Explainable Recommendation responses
- Multi-step Agent Plans and trace steps
"""
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict, field_validator

from backend.domain.marketplace import AvailabilityState


class ConstraintOperator(str, Enum):
    GTE = "gte"        # >=
    LTE = "lte"        # <=
    EQ = "eq"          # ==
    NEQ = "neq"        # !=
    CONTAINS = "contains"
    IN = "in"


class ObjectiveType(str, Enum):
    BEST_VALUE = "BEST_VALUE"
    MAX_PERFORMANCE = "MAX_PERFORMANCE"
    LOWEST_PRICE = "LOWEST_PRICE"
    FASTEST_DELIVERY = "FASTEST_DELIVERY"
    HIGHEST_RATED = "HIGHEST_RATED"
    BALANCED = "BALANCED"


class DeliveryPreference(str, Enum):
    FASTEST = "FASTEST"
    CHEAPEST = "CHEAPEST"
    BALANCED = "BALANCED"


class SpecificationConstraint(BaseModel):
    """
    Represents a discrete specification filter or preference.
    """
    key: str = Field(..., description="Spec key, e.g. ram_gb, ssd_gb, gpu, display_hz, battery_wh, weight_kg")
    operator: ConstraintOperator = Field(default=ConstraintOperator.GTE, description="Comparison operator")
    target_value: Any = Field(..., description="Target threshold or expected value")
    is_hard_constraint: bool = Field(default=True, description="True = hard filter (reject if not met); False = soft preference")
    unit: Optional[str] = Field(default=None, description="e.g. GB, TB, Hz, W, kg, inches, hours")
    description: Optional[str] = None


class BudgetConstraint(BaseModel):
    """
    Structured nested budget boundary container.
    """
    min: Optional[Decimal] = None
    max: Optional[Decimal] = None
    currency: str = "INR"


class ShoppingIntent(BaseModel):
    """
    Structured shopping goal extracted from natural language user input.
    """
    raw_query: str
    category: str = Field(default="laptops", description="Target product category (laptops, smartphones, headphones, monitors, etc.)")
    query: Optional[str] = Field(default=None, description="Cleaned search query keyword")
    purpose: Optional[str] = Field(default=None, description="e.g. AI/ML development, Esports Gaming, Office Productivity")
    target_use_case: Optional[str] = Field(default=None, description="Alias for purpose")
    quantity: int = Field(default=1, ge=1, description="Quantity of units requested")
    
    # Financial Constraints (Strict Decimals)
    budget_max: Optional[Decimal] = Field(default=None, description="Maximum budget threshold in INR")
    budget_min: Optional[Decimal] = Field(default=None, description="Minimum price filter in INR")
    currency: str = "INR"
    
    # Technical Specifications
    spec_constraints: List[SpecificationConstraint] = Field(default_factory=list)
    required_keywords: List[str] = Field(default_factory=list)
    excluded_keywords: List[str] = Field(default_factory=list)
    
    # Soft Preferences
    brand_preferences: List[str] = Field(default_factory=list)
    merchant_preferences: List[str] = Field(default_factory=list, description="Preferred merchant codes, e.g. ['AMAZON', 'FLIPKART', 'CROMA']")
    delivery_preference: DeliveryPreference = Field(default=DeliveryPreference.BALANCED)
    min_rating: float = Field(default=4.0, ge=1.0, le=5.0)
    require_in_stock: bool = Field(default=True)
    objective: ObjectiveType = Field(default=ObjectiveType.BEST_VALUE)
    
    # Ambiguity & Clarification Flag
    is_ambiguous: bool = Field(default=False)
    clarification_needed: Optional[str] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def validate_budget_bounds(cls, b_min: Optional[Decimal], b_max: Optional[Decimal]) -> None:
        if b_min is not None and b_min < Decimal("0.00"):
            raise ValueError("budget_min cannot be negative")
        if b_max is not None and b_max < Decimal("0.00"):
            raise ValueError("budget_max cannot be negative")
        if b_min is not None and b_max is not None and b_min > b_max:
            raise ValueError(f"Impossible budget range: budget_min ({b_min}) exceeds budget_max ({b_max})")

    def model_post_init(self, __context: Any) -> None:
        self.validate_budget_bounds(self.budget_min, self.budget_max)
        if self.quantity < 1:
            raise ValueError("quantity must be at least 1")
        if not self.query and self.category:
            self.query = self.category
        if not self.target_use_case and self.purpose:
            self.target_use_case = self.purpose
        elif not self.purpose and self.target_use_case:
            self.purpose = self.target_use_case

    @property
    def budget(self) -> BudgetConstraint:
        return BudgetConstraint(min=self.budget_min, max=self.budget_max, currency=self.currency)

    @property
    def hard_constraints(self) -> Dict[str, Any]:
        return {
            "budget_max": self.budget_max,
            "budget_min": self.budget_min,
            "currency": self.currency,
            "require_in_stock": self.require_in_stock,
            "specifications": [c for c in self.spec_constraints if c.is_hard_constraint],
            "required_keywords": self.required_keywords,
            "excluded_keywords": self.excluded_keywords
        }

    @property
    def preferences(self) -> Dict[str, Any]:
        return {
            "brand_preferences": self.brand_preferences,
            "merchant_preferences": self.merchant_preferences,
            "delivery_preference": self.delivery_preference,
            "min_rating": self.min_rating,
            "objective": self.objective,
            "soft_specifications": [c for c in self.spec_constraints if not c.is_hard_constraint]
        }


class AgentIntentRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="Natural language shopping prompt")
    message: Optional[str] = Field(default=None, description="Alternative alias for query")
    previous_intent: Optional[ShoppingIntent] = Field(default=None, description="Previous turn intent for refinement")

    def get_query_text(self) -> str:
        text = self.query or self.message
        if not text or not text.strip():
            raise ValueError("Query or message must be provided and non-empty.")
        return text.strip()


class AgentIntentResponse(BaseModel):
    intent: ShoppingIntent
    status: str = "VALID"  # "VALID", "AMBIGUOUS", "INVALID"
    message: str = "Intent extracted successfully"
    latency_ms: int = 0


class NormalizedProductCandidate(BaseModel):
    """
    Universal normalized product representation across Amazon, Flipkart, Croma.
    """
    id: str
    merchant_code: str
    merchant_name: str
    merchant_id: Optional[str] = None
    product_id: str
    sku: str
    title: str
    brand: str
    category: str
    model: Optional[str] = None
    description: Optional[str] = None
    
    # Monetary fields (Strict Decimals)
    current_price: Decimal
    base_price: Decimal
    discount_percentage: float = 0.0
    currency: str = "INR"
    
    # Inventory & Logistics
    inventory_state: AvailabilityState = AvailabilityState.IN_STOCK
    available_quantity: int = 0
    in_stock: bool = True
    delivery_days: int = 3
    shipping_cost: Decimal = Decimal("0.00")
    shipping_option_name: Optional[str] = None
    shipping_options: List[Dict[str, Any]] = Field(default_factory=list)
    rating: float = 4.5
    review_count: int = 0
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    
    # Extracted technical specifications
    specs: Dict[str, Any] = Field(default_factory=dict)
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("current_price", "base_price", mode="before")
    @classmethod
    def validate_non_negative_price(cls, v: Any) -> Decimal:
        if v is None:
            raise ValueError("Price cannot be None")
        d = Decimal(str(v))
        if d < Decimal("0.00"):
            raise ValueError(f"Price cannot be negative: {d}")
        return d


class MerchantOffer(BaseModel):
    """
    Merchant offer capturing price, inventory, logistics, and rating for a specific seller.
    """
    merchant_code: str
    merchant_name: str
    merchant_id: Optional[str] = None
    product_id: str
    sku: str
    current_price: Decimal
    base_price: Decimal
    currency: str = "INR"
    discount_percentage: float = 0.0
    inventory_state: AvailabilityState = AvailabilityState.IN_STOCK
    available_quantity: int = 0
    in_stock: bool = True
    delivery_days: int = 3
    shipping_cost: Decimal = Decimal("0.00")
    shipping_option_name: Optional[str] = None
    shipping_options: List[Dict[str, Any]] = Field(default_factory=list)
    rating: float = 4.5
    review_count: int = 0
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    specs: Dict[str, Any] = Field(default_factory=dict)
    source_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("current_price", "base_price", mode="before")
    @classmethod
    def validate_non_negative_price(cls, v: Any) -> Decimal:
        if v is None:
            raise ValueError("Price cannot be None")
        d = Decimal(str(v))
        if d < Decimal("0.00"):
            raise ValueError(f"Price cannot be negative: {d}")
        return d


class CanonicalProduct(BaseModel):
    """
    Canonical product representation grouping multiple merchant offers for the same underlying product model.
    """
    canonical_id: str
    title: str
    brand: str
    category: str
    model: Optional[str] = None
    description: Optional[str] = None
    normalized_specs: Dict[str, Any] = Field(default_factory=dict)
    offers: List[MerchantOffer] = Field(default_factory=list)
    best_price_offer: Optional[MerchantOffer] = None
    fastest_delivery_offer: Optional[MerchantOffer] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ConstraintViolation(BaseModel):
    """
    Structured machine-readable constraint violation description.
    """
    constraint: str
    reason_code: str
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None


class ConstraintEvaluation(BaseModel):
    """
    Structured constraint evaluation record for a single candidate.
    """
    candidate_id: str
    product_id: Optional[str] = None
    merchant_code: Optional[str] = None
    passed: bool
    violations: List[ConstraintViolation] = Field(default_factory=list)
    evaluated_constraints: List[str] = Field(default_factory=list)
    unknown_constraints: List[str] = Field(default_factory=list)
    soft_penalties: List[str] = Field(default_factory=list)


class ConstraintEvaluationResult(BaseModel):
    """
    Detailed audit result for constraint evaluation on a single candidate.
    Preserves both legacy list strings and machine-readable violation models.
    """
    candidate_id: str
    product_id: Optional[str] = None
    merchant_code: Optional[str] = None
    passed_all_hard_constraints: bool = True
    passed: bool = True
    violations: List[ConstraintViolation] = Field(default_factory=list)
    passed_constraints: List[str] = Field(default_factory=list)
    failed_constraints: List[str] = Field(default_factory=list)
    unknown_constraints: List[str] = Field(default_factory=list)
    soft_penalties: List[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.passed or self.failed_constraints or self.violations:
            self.passed = False
            self.passed_all_hard_constraints = False
        else:
            self.passed = True
            self.passed_all_hard_constraints = True


class ConstraintFilterRequest(BaseModel):
    intent: ShoppingIntent
    products: List[NormalizedProductCandidate] = Field(default_factory=list)


class ConstraintFilterResult(BaseModel):
    total_input: int
    total_passed: int
    total_rejected: int
    passed_candidates: List[NormalizedProductCandidate] = Field(default_factory=list)
    rejected_candidates: List[NormalizedProductCandidate] = Field(default_factory=list)
    evaluations: List[ConstraintEvaluationResult] = Field(default_factory=list)
    rejection_summary: Dict[str, int] = Field(default_factory=dict)
    execution_time_ms: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MCDAScoreBreakdown(BaseModel):
    """
    Detailed multi-criteria scoring breakdown on a 0.0 - 10.0 scale.
    """
    performance_score: float = Field(..., ge=0.0, le=10.0)
    price_efficiency_score: float = Field(..., ge=0.0, le=10.0)
    delivery_score: float = Field(..., ge=0.0, le=10.0)
    rating_score: float = Field(..., ge=0.0, le=10.0)
    brand_affinity_score: float = Field(..., ge=0.0, le=10.0)
    composite_score: float = Field(..., ge=0.0, le=10.0)
    score_justification: Dict[str, Any] = Field(default_factory=dict)


class RecommendationItem(BaseModel):
    """
    A single recommended product candidate with score and verified reasons.
    """
    rank: int
    badge: str = Field(..., description="e.g. 'TOP_PICK', 'BEST_VALUE', 'FASTEST_DELIVERY', 'RUNNER_UP'")
    candidate: NormalizedProductCandidate
    mcda_score: MCDAScoreBreakdown
    reasons: List[str] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    highlights: Dict[str, Any] = Field(default_factory=dict)


class AgentPlanStep(BaseModel):
    step_number: int
    step_name: str
    agent_or_tool: str
    description: str
    status: str = "PENDING"  # "PENDING", "RUNNING", "COMPLETED", "FAILED"


class AgentPlan(BaseModel):
    goal: str
    total_steps: int
    steps: List[AgentPlanStep] = Field(default_factory=list)


class AgentAction(str, Enum):
    DISCOVER_PRODUCTS = "DISCOVER_PRODUCTS"
    NORMALIZE_PRODUCTS = "NORMALIZE_PRODUCTS"
    APPLY_CONSTRAINTS = "APPLY_CONSTRAINTS"
    RANK_PRODUCTS = "RANK_PRODUCTS"
    GENERATE_RECOMMENDATION = "GENERATE_RECOMMENDATION"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"


PHASE_3_ALLOWED_ACTIONS = {
    AgentAction.DISCOVER_PRODUCTS,
    AgentAction.NORMALIZE_PRODUCTS,
    AgentAction.APPLY_CONSTRAINTS,
    AgentAction.RANK_PRODUCTS,
    AgentAction.GENERATE_RECOMMENDATION,
    AgentAction.REQUEST_CLARIFICATION,
    AgentAction.COMPLETE,
    AgentAction.FAIL
}


class PlanStep(BaseModel):
    id: str
    action: AgentAction
    description: str
    status: str = "PENDING"  # "PENDING", "RUNNING", "COMPLETED", "FAILED", "SKIPPED"
    error: Optional[str] = None
    execution_time_ms: int = 0


class ExecutionPlan(BaseModel):
    goal: str
    total_steps: int
    steps: List[PlanStep] = Field(default_factory=list)
    status: str = "PLANNED"  # "PLANNED", "EXECUTING", "COMPLETED", "FAILED"

    def validate_actions(self) -> None:
        for s in self.steps:
            if s.action not in PHASE_3_ALLOWED_ACTIONS:
                raise ValueError(f"Unauthorized or unknown action: {s.action}")


class AgentTraceStep(BaseModel):
    step_id: str
    title: str
    agent_name: str
    status: str = "completed"
    summary: str
    details: Optional[Dict[str, Any]] = None
    execution_time_ms: int = 0


class ShoppingAgentState(BaseModel):
    session_id: str
    user_message: str
    user_id: str = "default_user"
    shopping_intent: Optional[ShoppingIntent] = None
    execution_plan: Optional[ExecutionPlan] = None
    current_step_index: int = 0
    status: str = "PENDING"  # "PENDING", "PLANNING", "DISCOVERING", "CLARIFICATION_REQUIRED", "COMPLETED", "FAILED"
    discovered_products: List[NormalizedProductCandidate] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_steps: List[AgentTraceStep] = Field(default_factory=list)
    timestamps: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentSessionRequest(BaseModel):
    message: Optional[str] = Field(default=None, description="User shopping query")
    query: Optional[str] = Field(default=None, description="Alias for message")
    session_id: Optional[str] = None
    user_id: str = "default_user"

    def get_message_text(self) -> str:
        text = self.message or self.query
        if not text or not text.strip():
            raise ValueError("Message or query must be provided and non-empty.")
        return text.strip()


class AgentSessionResponse(BaseModel):
    session_id: str
    status: str
    intent: Optional[ShoppingIntent] = None
    plan: Optional[ExecutionPlan] = None
    discovered_count: int = 0
    trace: List[AgentTraceStep] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    latency_ms: int = 0


class RecommendationResponse(BaseModel):
    """
    Final synthesized recommendation output for user review and authorization.
    """
    session_id: str
    task_id: Optional[str] = None
    intent: ShoppingIntent
    plan: AgentPlan
    total_candidates_discovered: int
    candidates_passing_constraints: int
    top_recommendation: Optional[RecommendationItem] = None
    best_value_recommendation: Optional[RecommendationItem] = None
    fastest_delivery_recommendation: Optional[RecommendationItem] = None
    all_recommendations: List[RecommendationItem] = Field(default_factory=list)
    rejected_candidates_summary: Dict[str, int] = Field(default_factory=dict)
    trace: List[AgentTraceStep] = Field(default_factory=list)
    requires_human_authorization: bool = True
    authorization_reason: str = "Review top recommendation and confirm merchant checkout."


class MerchantDiscoveryStatus(BaseModel):
    merchant: str
    status: str  # "SUCCESS", "FAILED", "TIMEOUT", "SKIPPED"
    result_count: int = 0
    error: Optional[str] = None
    latency_ms: int = 0


class DiscoveryRequest(BaseModel):
    intent: Optional[ShoppingIntent] = None
    query: Optional[str] = None
    message: Optional[str] = None
    category: Optional[str] = None
    merchants: Optional[List[str]] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    in_stock_only: bool = False
    session_id: Optional[str] = None
    user_id: str = "default_user"

    def get_search_query(self) -> str:
        if self.intent and (self.intent.query or self.intent.raw_query):
            return self.intent.query or self.intent.raw_query
        text = self.query or self.message
        if text and text.strip():
            return text.strip()
        if self.category:
            return self.category.strip()
        return "laptops"


class DiscoveryResult(BaseModel):
    products: List[NormalizedProductCandidate] = Field(default_factory=list)
    canonical_products: List[CanonicalProduct] = Field(default_factory=list)
    merchants_attempted: List[str] = Field(default_factory=list)
    merchants_succeeded: List[str] = Field(default_factory=list)
    merchants_failed: List[Dict[str, Any]] = Field(default_factory=list)
    merchant_statuses: List[MerchantDiscoveryStatus] = Field(default_factory=list)
    total_results: int = 0
    partial_results: bool = False
    errors: List[str] = Field(default_factory=list)
    execution_time_ms: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)
