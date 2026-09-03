"""
Layer 2: Agent Brain - Context Store
Maintains short-term conversational context, working memory scratchpad,
multi-turn criteria refinement, and persistent user preferences.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from backend.schemas import UserRequirements, Product

class UserProfile(BaseModel):
    user_id: str = "user_default"
    name: str = "Rahul N."
    default_shipping_address: str = "Rahul N., Flat 402, HighTech Tech Park, Bangalore 560100"
    preferred_payment_method: str = "UPI_TOKEN_4829"
    brand_affinity: List[str] = ["ASUS", "Apple", "Lenovo"]
    preferred_delivery_max_days: int = 3
    default_max_budget_inr: float = 150000.0

class SessionContext(BaseModel):
    session_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    active_requirements: Optional[UserRequirements] = None
    query_history: List[str] = []
    shortlisted_products: List[Product] = []
    agent_scratchpad: Dict[str, Any] = {}
    last_recommended_product: Optional[Product] = None
    active_stage: str = "IDLE"  # IDLE, PLANNING, DISCOVERING, RANKING, NEGOTIATING, CHECKOUT, AUTHORIZED

# Global in-memory storage
SESSIONS: Dict[str, SessionContext] = {}
PROFILES: Dict[str, UserProfile] = {
    "user_default": UserProfile()
}

class ContextStore:
    @staticmethod
    def get_or_create_session(session_id: str = "session_default") -> SessionContext:
        if session_id not in SESSIONS:
            SESSIONS[session_id] = SessionContext(session_id=session_id)
        return SESSIONS[session_id]

    @staticmethod
    def get_user_profile(user_id: str = "user_default") -> UserProfile:
        return PROFILES.get(user_id, PROFILES["user_default"])

    @staticmethod
    def update_session_requirements(session_id: str, reqs: UserRequirements) -> SessionContext:
        session = ContextStore.get_or_create_session(session_id)
        session.active_requirements = reqs
        session.query_history.append(reqs.raw_query)
        session.updated_at = datetime.now(timezone.utc).isoformat()
        return session

    @staticmethod
    def set_scratchpad_value(session_id: str, key: str, value: Any):
        session = ContextStore.get_or_create_session(session_id)
        session.agent_scratchpad[key] = value
        session.updated_at = datetime.now(timezone.utc).isoformat()

    @staticmethod
    def get_scratchpad_value(session_id: str, key: str, default: Any = None) -> Any:
        session = ContextStore.get_or_create_session(session_id)
        return session.agent_scratchpad.get(key, default)

    @staticmethod
    def set_active_stage(session_id: str, stage: str):
        session = ContextStore.get_or_create_session(session_id)
        session.active_stage = stage
        session.updated_at = datetime.now(timezone.utc).isoformat()
