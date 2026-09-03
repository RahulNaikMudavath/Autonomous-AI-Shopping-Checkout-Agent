"""
Test Suite for Universal Live Discovery Engine across Any Product Category
"""
import pytest
from backend.schemas import UserRequirements
from backend.agent.live_discovery_engine import LiveDiscoveryEngine
from backend.agent.subagents.discovery_agent import DiscoveryAgent
from backend.agent.subagents.ranking_agent import RankingAgent
from backend.config import get_settings, update_runtime_settings

def test_live_discovery_audio_category():
    reqs = UserRequirements(
        raw_query="Find me the best noise cancelling headphones under 30000 with long battery life",
        budget_max_inr=30000.0,
        category="audio"
    )
    products, trace = DiscoveryAgent.discover_candidates(reqs)
    assert len(products) >= 2
    assert any("Sony" in p.brand or "Sennheiser" in p.brand for p in products)
    assert any(p.price_inr <= 30000.0 for p in products)

    # Test ranking
    scored, top_pick, _ = RankingAgent.rank_and_evaluate(products, reqs)
    assert top_pick is not None
    assert top_pick.price_inr <= 30000.0

def test_live_discovery_smartphone_category():
    reqs = UserRequirements(
        raw_query="I need a flagship 5G smartphone with good camera under 1.2 lakh",
        budget_max_inr=120000.0,
        category="smartphones"
    )
    products, trace = DiscoveryAgent.discover_candidates(reqs)
    assert len(products) >= 2
    assert any("Apple" in p.brand or "Samsung" in p.brand for p in products)

def test_live_discovery_monitor_category():
    reqs = UserRequirements(
        raw_query="4K 144Hz IPS gaming monitor under 50000",
        budget_max_inr=50000.0,
        category="monitors"
    )
    products, trace = DiscoveryAgent.discover_candidates(reqs)
    assert len(products) >= 2
    assert any("LG" in p.brand or "Samsung" in p.brand for p in products)

def test_runtime_settings_update():
    settings = get_settings()
    assert settings.live_discovery_mode in ["auto", "sandbox"]

    update_runtime_settings({"default_llm_provider": "openai", "live_discovery_mode": "auto"})
    new_settings = get_settings()
    assert new_settings.default_llm_provider == "openai"
    assert new_settings.live_discovery_mode == "auto"
