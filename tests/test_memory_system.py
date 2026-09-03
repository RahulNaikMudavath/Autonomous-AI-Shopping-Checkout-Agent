"""
Test Suite for 10. Memory (Multi-Tier Memory Architecture & Semantic Vector Retrieval)
"""
import pytest
from backend.agent.memory_manager import MemoryManager, UserProfileMemory
from backend.schemas import Product, ProductSpecs, UserRequirements
from backend.agent.subagents.ranking_agent import RankingAgent

def test_user_profile_memory():
    profile = MemoryManager.get_profile()
    assert profile.name == "Rahul Naik"
    assert "ASUS" in profile.preferred_brands
    assert "Logitech" in profile.preferred_brands
    assert profile.category_budgets["laptops"] == 120000.0

    # Test update
    updated = MemoryManager.update_profile({"preferred_brands": ["ASUS", "Lenovo", "Logitech", "Apple", "Framework"]})
    assert "Framework" in updated.preferred_brands

def test_transaction_memory():
    tx = MemoryManager.get_transactions()
    assert tx.total_orders_completed >= 3
    assert tx.total_lifetime_spend_inr > 100000.0
    assert any(t.has_return for t in tx.recent_transactions)
    assert any("Logitech" in t.item_title for t in tx.recent_transactions)

def test_agent_working_state_memory():
    working = MemoryManager.get_working_state()
    assert working.active_session_id == "session_default"
    assert "laptop" in working.scratchpad_notes["target_category"]
    assert working.scratchpad_notes["min_ram_gb"] == 32

def test_semantic_vector_memory_exact_prompts():
    # Prompt 1: "I prefer lightweight laptops"
    res1 = MemoryManager.search_semantic_memory("I need a lightweight laptop for travel", top_k=2)
    assert len(res1) > 0
    assert "lightweight" in res1[0].memory.content.lower()
    assert res1[0].similarity_score > 0.3

    # Prompt 2: "I usually buy Logitech peripherals"
    res2 = MemoryManager.search_semantic_memory("Show me a Logitech wireless mouse", top_k=2)
    assert len(res2) > 0
    assert "logitech" in res2[0].memory.content.lower()

    # Prompt 3: "Don't recommend refurbished products"
    res3 = MemoryManager.search_semantic_memory("Check if refurbished deals are okay", top_k=2)
    assert len(res3) > 0
    assert "refurbished" in res3[0].memory.content.lower()

def test_add_and_retrieve_semantic_memory():
    new_mem = MemoryManager.add_semantic_memory(
        content="Always check for Thunderbolt 4 or USB4 support for external eGPU.",
        category="connectivity_preference"
    )
    assert new_mem.id.startswith("mem_")

    search_res = MemoryManager.search_semantic_memory("Thunderbolt 4 eGPU dock", top_k=1)
    assert len(search_res) > 0
    assert "Thunderbolt" in search_res[0].memory.content

def test_ranking_agent_semantic_fusion():
    p1 = Product(
        id="test-lap-1",
        merchant_id="merchant-a",
        merchant_name="Merchant A",
        title="Lightweight Slim AI Notebook",
        brand="ASUS",
        category="laptop",
        price_inr=95000.0,
        original_price_inr=110000.0,
        discount_percent=13.6,
        in_stock=True,
        rating=4.8,
        review_count=120,
        specs=ProductSpecs(
            cpu="Intel Core Ultra 7",
            gpu="NVIDIA RTX 4060",
            ram_gb=32,
            ssd_gb=1000,
            battery_wh=75,
            battery_life_hours=8.5,
            display_inches=15.6,
            weight_kg=1.85
        )
    )

    reqs = UserRequirements(
        raw_query="I need a lightweight laptop for AI development under 1.2 lakh",
        category="laptop",
        budget_max_inr=120000.0,
        objective="best_value"
    )

    scored, top, trace = RankingAgent.rank_and_evaluate([p1], reqs)
    assert len(scored) == 1
    assert scored[0].value_score is not None
    assert "semantic_memory_applied" in scored[0].value_breakdown
