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
from pydantic import BaseModel, Field, ConfigDict

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
    description: Optional[str] = None


class ShoppingIntent(BaseModel):
    """
    Structured shopping goal extracted from natural language user input.
    """
    raw_query: str
    category: str = Field(default="laptops", description="Target product category (laptops, smartphones, headphones, monitors, etc.)")
    target_use_case: Optional[str] = Field(default=None, description="e.g. AI/ML development, Esports Gaming, Office Productivity")
    
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


class NormalizedProductCandidate(BaseModel):
    """
    Universal normalized product representation across Amazon, Flipkart, Croma.
    """
    id: str
    merchant_code: str
    merchant_name: str
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
    rating: float = 4.5
    review_count: int = 0
    image_url: Optional[str] = None
    
    # Extracted technical specifications
    specs: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ConstraintEvaluationResult(BaseModel):
    """
    Detailed audit result for constraint evaluation on a single candidate.
    """
    candidate_id: str
    passed_all_hard_constraints: bool
    passed_constraints: List[str] = Field(default_factory=list)
    failed_constraints: List[str] = Field(default_factory=list)
    soft_penalties: List[str] = Field(default_factory=list)


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


class AgentTraceStep(BaseModel):
    step_id: str
    title: str
    agent_name: str
    status: str = "completed"
    summary: str
    details: Optional[Dict[str, Any]] = None
    execution_time_ms: int = 0


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
