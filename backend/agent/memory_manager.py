"""
Layer 2: Agent Intelligence - Multi-Tier Memory Subsystem
Manages 4 distinct memory tiers for the Autonomous AI Shopping Agent:

1. User Profile Memory (Preferences, Brands, Budgets, Sizing, Shipping)
2. Transaction Memory (Order History, Returns, RMAs, Spending Analytics)
3. Agent Working Memory (Episodic DAG State, Multi-Merchant Cart, Auth Mandates)
4. Semantic Vector Memory (Vector DB with Similarity Retrieval for Natural Language Rules)
"""
import math
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field

from backend.schemas import Product, Order
from backend.trust_safety.policy_engine import add_audit_log

# -------------------------------------------------------------
# Tier 1: User Profile Memory Models
# -------------------------------------------------------------
class UserProfileMemory(BaseModel):
    user_id: str = "usr_rahul_001"
    name: str = "Rahul Naik"
    preferred_brands: List[str] = ["ASUS", "Lenovo", "Logitech", "Apple", "Sony"]
    category_budgets: Dict[str, float] = {
        "laptops": 120000.0,
        "electronics": 25000.0,
        "groceries": 3000.0,
        "peripherals": 15000.0
    }
    sizes: Dict[str, str] = {
        "laptop_screen": "16-inch",
        "apparel": "L",
        "footwear": "US 10"
    }
    preferred_categories: List[str] = ["Laptops", "AI Workstations", "Peripherals", "Developer Tech"]
    shipping_preferences: Dict[str, str] = {
        "address": "Flat 402, HighTech Residency, Outer Ring Road, Bangalore - 560103",
        "delivery_speed": "Express Priority (1-2 Days)",
        "allow_weekend_delivery": "true"
    }

# -------------------------------------------------------------
# Tier 2: Transaction Memory Models
# -------------------------------------------------------------
class TransactionRecord(BaseModel):
    order_id: str
    item_title: str
    category: str
    merchant_name: str
    amount_inr: float
    status: str
    purchased_at: str
    has_return: bool = False
    return_reason: Optional[str] = None

class TransactionMemory(BaseModel):
    total_lifetime_spend_inr: float = 237490.0
    total_orders_completed: int = 4
    total_returns_processed: int = 1
    recent_transactions: List[TransactionRecord] = [
        TransactionRecord(
            order_id="ORD-TECH-9948",
            item_title="ASUS ROG Strix G16 (i7-14650HX, 32GB RAM, RTX 4070)",
            category="laptops",
            merchant_name="Merchant A (TechHub)",
            amount_inr=109999.0,
            status="DELIVERED",
            purchased_at="2026-08-20T14:30:00Z"
        ),
        TransactionRecord(
            order_id="ORD-ELEC-4412",
            item_title="Logitech MX Master 3S Wireless Mouse",
            category="peripherals",
            merchant_name="Merchant B (ElectroBazaar)",
            amount_inr=8995.0,
            status="DELIVERED",
            purchased_at="2026-08-24T11:15:00Z"
        ),
        TransactionRecord(
            order_id="ORD-OMNI-2219",
            item_title="Dell UltraSharp 27-inch 4K Monitor",
            category="electronics",
            merchant_name="Merchant C (OmniStore)",
            amount_inr=48500.0,
            status="DELIVERED",
            purchased_at="2026-08-29T16:45:00Z"
        ),
        TransactionRecord(
            order_id="ORD-PRO-1102",
            item_title="Mechanical Gaming Keyboard (Defective Switch)",
            category="peripherals",
            merchant_name="Merchant D (ProHardware)",
            amount_inr=6999.0,
            status="RETURNED_AND_REFUNDED",
            purchased_at="2026-08-15T09:00:00Z",
            has_return=True,
            return_reason="Keycap switch malfunction on spacebar"
        )
    ]

# -------------------------------------------------------------
# Tier 3: Agent Working / Episodic State Memory
# -------------------------------------------------------------
class AgentWorkingMemory(BaseModel):
    active_session_id: str = "session_default"
    active_task: str = "Autonomous Laptop Evaluation & Value Optimization"
    current_dag_stage: str = "CHECKOUT_AUTHORIZATION"
    current_cart_item_count: int = 1
    current_merchant_lock: str = "Merchant A (TechHub)"
    current_delegated_mandate_id: Optional[str] = "AUTH_MANDATE_9488219A"
    last_checkpoint_timestamp: str = "2026-09-04T00:05:00Z"
    scratchpad_notes: Dict[str, Any] = {
        "target_category": "laptop",
        "min_ram_gb": 32,
        "gpu_preference": "NVIDIA RTX",
        "budget_limit": 120000.0
    }

# -------------------------------------------------------------
# Tier 4: Semantic Vector Memory (Vector DB)
# -------------------------------------------------------------
class SemanticMemoryItem(BaseModel):
    id: str
    content: str
    category: str
    importance: float = 0.9
    created_at: str
    source: str = "USER_DIRECTIVE"

class SemanticSearchResult(BaseModel):
    memory: SemanticMemoryItem
    similarity_score: float

class SemanticVectorMemory:
    """
    Lightweight, high-performance in-memory Vector DB with cosine similarity retrieval.
    """
    def __init__(self):
        self.memories: List[SemanticMemoryItem] = [
            SemanticMemoryItem(
                id="mem_01",
                content="I prefer lightweight laptops under 2.2kg for portable AI development.",
                category="hardware_preference",
                importance=0.95,
                created_at="2026-08-01T10:00:00Z"
            ),
            SemanticMemoryItem(
                id="mem_02",
                content="I usually buy Logitech peripherals because of ergonomic reliability.",
                category="brand_preference",
                importance=0.92,
                created_at="2026-08-05T12:00:00Z"
            ),
            SemanticMemoryItem(
                id="mem_03",
                content="Don't recommend refurbished or open-box products under any circumstance.",
                category="exclusion_rule",
                importance=0.98,
                created_at="2026-08-10T15:30:00Z"
            ),
            SemanticMemoryItem(
                id="mem_04",
                content="Always verify minimum 3-year manufacturer onsite warranty.",
                category="warranty_rule",
                importance=0.88,
                created_at="2026-08-12T09:15:00Z"
            ),
            SemanticMemoryItem(
                id="mem_05",
                content="Prioritize matte display finish over glossy reflective screens.",
                category="display_preference",
                importance=0.80,
                created_at="2026-08-18T18:00:00Z"
            )
        ]

    def _tokenize_vector(self, text: str) -> Dict[str, float]:
        """Simple TF-IDF style token frequency vector."""
        tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
        vec = {}
        for tok in tokens:
            vec[tok] = vec.get(tok, 0.0) + 1.0
        # Normalize
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {k: v / norm for k, v in vec.items()}

    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        dot = sum(vec1.get(k, 0.0) * vec2.get(k, 0.0) for k in vec1)
        return round(dot, 4)

    def search(self, query: str, top_k: int = 3, min_similarity: float = 0.05) -> List[SemanticSearchResult]:
        q_vec = self._tokenize_vector(query)
        results = []

        for mem in self.memories:
            mem_vec = self._tokenize_vector(mem.content)
            sim = self._cosine_similarity(q_vec, mem_vec)

            # Keyword boost heuristic
            for word in ["laptop", "lightweight", "logitech", "refurbished", "warranty", "peripheral", "matte"]:
                if word in query.lower() and word in mem.content.lower():
                    sim = min(1.0, sim + 0.35)

            if sim >= min_similarity:
                results.append(SemanticSearchResult(memory=mem, similarity_score=sim))

        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:top_k]

    def add_memory(self, content: str, category: str = "general_preference", importance: float = 0.9) -> SemanticMemoryItem:
        mem = SemanticMemoryItem(
            id=f"mem_{int(time.time() * 1000)}",
            content=content,
            category=category,
            importance=importance,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            source="USER_INTERACTION"
        )
        self.memories.append(mem)
        return mem

# -------------------------------------------------------------
# High-Level Memory Manager
# -------------------------------------------------------------
class MemoryManager:
    _profile: UserProfileMemory = UserProfileMemory()
    _transactions: TransactionMemory = TransactionMemory()
    _working_state: AgentWorkingMemory = AgentWorkingMemory()
    _semantic_vector: SemanticVectorMemory = SemanticVectorMemory()

    @classmethod
    def get_all_memory(cls) -> Dict[str, Any]:
        """Aggregates all 4 memory tiers into a unified view."""
        return {
            "tier_1_user_profile": cls._profile.model_dump(),
            "tier_2_transactions": cls._transactions.model_dump(),
            "tier_3_working_state": cls._working_state.model_dump(),
            "tier_4_semantic_vector_count": len(cls._semantic_vector.memories),
            "tier_4_semantic_memories": [m.model_dump() for m in cls._semantic_vector.memories]
        }

    @classmethod
    def get_profile(cls) -> UserProfileMemory:
        return cls._profile

    @classmethod
    def update_profile(cls, new_profile_data: Dict[str, Any]) -> UserProfileMemory:
        for k, v in new_profile_data.items():
            if hasattr(cls._profile, k):
                setattr(cls._profile, k, v)
        add_audit_log(
            action_type="USER_PROFILE_MEMORY_UPDATED",
            actor="USER",
            payload_summary=f"Updated preferences for {cls._profile.name}",
            policy_verified=True
        )
        return cls._profile

    @classmethod
    def get_transactions(cls) -> TransactionMemory:
        return cls._transactions

    @classmethod
    def get_working_state(cls) -> AgentWorkingMemory:
        return cls._working_state

    @classmethod
    def search_semantic_memory(cls, query: str, top_k: int = 3) -> List[SemanticSearchResult]:
        return cls._semantic_vector.search(query=query, top_k=top_k)

    @classmethod
    def add_semantic_memory(cls, content: str, category: str = "user_preference") -> SemanticMemoryItem:
        mem = cls._semantic_vector.add_memory(content=content, category=category)
        add_audit_log(
            action_type="SEMANTIC_MEMORY_INGESTED",
            actor="VECTOR_DB",
            payload_summary=f"Ingested semantic preference: '{content}' (Category: {category})",
            policy_verified=True
        )
        return mem
