"""
Comprehensive Test Suite for 2. The Agent Brain
Tests ContextStore, IntentExtractor, TaskPlanner, Subagents (Discovery, Ranking, Merchant),
AgentSupervisor, and Stage-Gated Checkout Pipeline.
"""
import pytest
from backend.agent.context_store import ContextStore, UserProfile
from backend.agent.intent_extractor import IntentExtractor
from backend.agent.task_planner import TaskPlanner
from backend.agent.subagents.discovery_agent import DiscoveryAgent
from backend.agent.subagents.ranking_agent import RankingAgent
from backend.agent.subagents.merchant_agent import MerchantAgent
from backend.agent.supervisor import AgentSupervisor
from backend.agent.checkout_pipeline import CheckoutPipeline
from backend.schemas import Product, ProductSpecs

def test_context_store_and_user_profile():
    session_id = "test_session_abc"
    session = ContextStore.get_or_create_session(session_id)
    assert session.session_id == session_id
    assert session.active_stage == "IDLE"

    profile = ContextStore.get_user_profile()
    assert "ASUS" in profile.brand_affinity
    assert profile.default_max_budget_inr > 0

    ContextStore.set_scratchpad_value(session_id, "test_key", 42)
    assert ContextStore.get_scratchpad_value(session_id, "test_key") == 42

def test_intent_extractor_core_and_refinement():
    session_id = "test_session_multiturn"
    
    # Turn 1: Initial broad query
    turn1 = "I need an AI laptop under 1.2 lakh with 32GB RAM"
    action1, reqs1 = IntentExtractor.extract_intent_and_constraints(turn1, session_id)
    assert action1 == "NEW_SEARCH"
    assert reqs1.budget_max_inr == 120000.0
    assert reqs1.min_ram_gb == 32
    assert reqs1.gpu_brand_preference == "NVIDIA"

    # Turn 2: Criteria refinement
    turn2 = "Also make it with 1TB SSD and prefer good battery life"
    action2, reqs2 = IntentExtractor.extract_intent_and_constraints(turn2, session_id)
    assert action2 == "REFINE_CRITERIA"
    assert reqs2.budget_max_inr == 120000.0 # preserved from turn 1
    assert reqs2.min_ram_gb == 32 # preserved
    assert reqs2.min_ssd_gb == 1024
    assert reqs2.battery_priority == "high"

def test_task_planner():
    action_type, reqs = IntentExtractor.extract_intent_and_constraints("AI laptop under 1.2L")
    plan = TaskPlanner.generate_plan(action_type, reqs)
    
    step_names = [s.step_name for s in plan.steps]
    assert "POLICY_PRE_CHECK" in step_names
    assert "DISCOVERY_FEDERATED" in step_names
    assert "RANKING_MCDA" in step_names
    assert "MERCHANT_VERIFICATION" in step_names
    assert "SUPERVISOR_SYNTHESIS" in step_names

def test_discovery_agent():
    action_type, reqs = IntentExtractor.extract_intent_and_constraints("AI laptop with 32GB RAM under 1.2L")
    candidates, trace = DiscoveryAgent.discover_candidates(reqs)
    
    assert len(candidates) >= 3
    assert all(c.specs.ram_gb >= 16 for c in candidates)
    assert trace.step_id == "trace_discovery_agent"
    assert trace.status == "completed"

def test_ranking_agent():
    action_type, reqs = IntentExtractor.extract_intent_and_constraints(
        "I need a laptop for AI/ML development under ₹1.2 lakh. 32GB RAM minimum. NVIDIA GPU. 1TB SSD. Prefer good battery life. Find the best value."
    )
    candidates, _ = DiscoveryAgent.discover_candidates(reqs)
    ranked, top_pick, trace = RankingAgent.rank_and_evaluate(candidates, reqs)

    assert top_pick is not None
    assert top_pick.value_score >= 9.0
    assert "4070" in top_pick.specs.gpu
    assert trace.step_id == "trace_ranking_agent"

def test_merchant_agent():
    action_type, reqs = IntentExtractor.extract_intent_and_constraints("laptop under 1.2L")
    candidates, _ = DiscoveryAgent.discover_candidates(reqs)
    verified, trace = MerchantAgent.negotiate_and_verify(candidates)

    assert len(verified) == len(candidates)
    assert trace.step_id == "trace_merchant_agent"
    assert "verified_merchants" in trace.details

def test_agent_supervisor_full_pipeline():
    query = "I need a laptop for AI/ML development under ₹1.2 lakh. 32GB RAM minimum. NVIDIA GPU. 1TB SSD. Prefer good battery life. Find the best value."
    result = AgentSupervisor.process_request(query, session_id="test_supervisor_session")

    assert result.top_recommendation is not None
    assert "ROG Strix" in result.top_recommendation.title or "RTX 4070" in result.top_recommendation.specs.gpu
    assert len(result.trace) >= 6
    assert len(result.comparison_table) >= 3
    assert result.policy_status["passed"] is True

def test_checkout_pipeline_stage_gates():
    action_type, reqs = IntentExtractor.extract_intent_and_constraints("laptop under 1.2L")
    candidates, _ = DiscoveryAgent.discover_candidates(reqs)
    p = candidates[0]

    order, traces = CheckoutPipeline.execute_stage_gated_checkout(
        product=p,
        cart_id="test_cart_pipe",
        session_id="test_pipe_session",
        user_confirmed=True
    )

    assert order.order_id.startswith("ORD_")
    assert order.payment_status == "AUTHORIZED"
    assert order.order_status == "CONFIRMED"
    
    trace_titles = [t.title for t in traces]
    assert any("Stage 1: Cart" in t for t in trace_titles)
    assert any("Stage 2: Dynamic Checkout" in t for t in trace_titles)
    assert any("Stage 3: Spending & Policy Authorization" in t for t in trace_titles)
    assert any("Stage 4: Tokenized Payment" in t for t in trace_titles)
    assert any("Stage 5: Order Created" in t for t in trace_titles)
