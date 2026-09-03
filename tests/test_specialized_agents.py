"""
Test Suite for 3. Specialized Agents (Agent 1 Intent, Agent 2 Planner, Agent 3 Discovery & Merchant APIs)
"""
import pytest
from backend.agent.intent_agent import IntentAgent, StructuredIntentState
from backend.agent.planning_agent import PlanningAgent
from backend.agent.subagents.discovery_agent import DiscoveryAgent
from backend.agent.subagents.ranking_agent import RankingAgent
from backend.schemas import UserRequirements
from backend.infrastructure.merchants import PRODUCT_CATALOG

def test_agent1_intent_agent_exact_prompt():
    prompt = "I need a laptop for coding and AI under 1.2L"
    state = IntentAgent.parse_query_to_state(prompt)

    # Validate exact structure
    assert state.category == "laptop"
    assert state.budget.max == 120000.0
    assert state.budget.currency == "INR"
    assert state.requirements.ram_gb.min == 32
    assert state.requirements.storage_gb.min == 1000
    assert state.requirements.gpu == "NVIDIA"
    assert state.optimization == "value"

    # Validate serialized dict matches expected schema
    state_dict = state.model_dump()
    assert state_dict == {
        "category": "laptop",
        "budget": {
            "max": 120000.0,
            "currency": "INR"
        },
        "requirements": {
            "ram_gb": {
                "min": 32
            },
            "storage_gb": {
                "min": 1000
            },
            "gpu": "NVIDIA",
            "battery_life_hours": None
        },
        "optimization": "value"
    }

def test_agent2_planning_agent_dag_execution():
    prompt = "I need a laptop for coding and AI under 1.2L"
    intent_state = IntentAgent.parse_query_to_state(prompt)

    reqs_adapter = UserRequirements(
        raw_query=prompt,
        budget_max_inr=intent_state.budget.max,
        min_ram_gb=intent_state.requirements.ram_gb.min,
        min_ssd_gb=intent_state.requirements.storage_gb.min,
        gpu_brand_preference="NVIDIA",
        objective="best_value"
    )

    def mock_discovery():
        return DiscoveryAgent.discover_candidates(reqs_adapter)

    def mock_ranking(candidates):
        return RankingAgent.rank_and_evaluate(candidates, reqs_adapter)

    res = PlanningAgent.execute_plan(
        intent_state=intent_state,
        discovery_fn=mock_discovery,
        ranking_fn=mock_ranking,
        cart_id="test_dag_cart"
    )

    # Validate exact 8 DAG steps
    step_names = [s.step_name for s in res.steps]
    expected_dag = [
        "Search merchants",
        "Normalize results",
        "Filter constraints",
        "Rank candidates",
        "Check availability",
        "Create cart",
        "Calculate final price",
        "Check authorization"
    ]
    assert step_names == expected_dag
    assert len(res.steps) == 8
    assert all(s.status == "completed" for s in res.steps)
    assert res.top_candidate is not None
    assert res.cart is not None
    assert res.quote is not None
    assert res.authorization_status.passed is True

def test_agent3_merchant_apis_structure():
    # Verify Merchant A products exist
    merchant_a_items = [p for p in PRODUCT_CATALOG if p.merchant_id == "techhub_in"]
    assert len(merchant_a_items) >= 1
    assert any("ROG Strix" in p.title for p in merchant_a_items)

    # Verify Merchant B products exist
    merchant_b_items = [p for p in PRODUCT_CATALOG if p.merchant_id == "electrobazaar_in"]
    assert len(merchant_b_items) >= 1
    assert any("Helios" in p.title for p in merchant_b_items)

    # Verify Merchant C products exist
    merchant_c_items = [p for p in PRODUCT_CATALOG if p.merchant_id == "omnistore_in"]
    assert len(merchant_c_items) >= 1

    # Verify Merchant D products exist
    merchant_d_items = [p for p in PRODUCT_CATALOG if p.merchant_id == "prohardware_in"]
    assert len(merchant_d_items) >= 1
    assert any("Alienware" in p.title for p in merchant_d_items)
