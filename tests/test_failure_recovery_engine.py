"""
Test Suite for 9. Failure Recovery (Distributed Resiliency & Autonomous Replanning Engine)
"""
import pytest
from backend.infrastructure.failure_recovery_engine import (
    FailureRecoveryEngine, FailureScenarioType
)

def test_price_change_autonomous_replanning():
    trace = FailureRecoveryEngine.simulate_recovery(FailureScenarioType.PRICE_CHANGED)
    assert trace.recovered_successfully is True
    assert trace.scenario == FailureScenarioType.PRICE_CHANGED
    assert len(trace.steps) >= 4
    
    # Check steps
    assert trace.steps[0].stage == "CHECKOUT_VERIFICATION"
    assert trace.steps[0].status == "FAILED"
    assert trace.steps[1].stage == "REPLANNING_DISCOVERY"
    assert trace.steps[1].status == "COMPLETED"
    assert trace.steps[2].stage == "RE_RANKING"
    assert "Lenovo Legion" in str(trace.steps[2].details)
    assert "Within Budget" in str(trace.steps[2].details)

def test_inventory_disappeared_recovery():
    trace = FailureRecoveryEngine.simulate_recovery(FailureScenarioType.INVENTORY_DISAPPEARED)
    assert trace.recovered_successfully is True
    assert trace.scenario == FailureScenarioType.INVENTORY_DISAPPEARED
    assert any("HP Omen" in str(s.details) for s in trace.steps)
    assert any("OmniStore" in str(s.details) for s in trace.steps)

def test_payment_failover_recovery():
    trace = FailureRecoveryEngine.simulate_recovery(FailureScenarioType.PAYMENT_FAILED)
    assert trace.recovered_successfully is True
    assert trace.scenario == FailureScenarioType.PAYMENT_FAILED
    assert any("pm_card_virtual" in str(s.details) or "TKN_VISA" in str(s.details) for s in trace.steps)
    assert any("SETTLED" in str(s.details) for s in trace.steps)

def test_merchant_timeout_exponential_backoff():
    trace = FailureRecoveryEngine.simulate_recovery(FailureScenarioType.MERCHANT_API_TIMEOUT)
    assert trace.recovered_successfully is True
    assert trace.scenario == FailureScenarioType.MERCHANT_API_TIMEOUT
    assert trace.steps[0].status == "RETRYING"
    assert trace.steps[1].status == "RETRYING"
    assert trace.steps[2].status == "COMPLETED"
    assert trace.steps[2].details["http_status"] == 200

def test_agent_tool_crash_checkpoint_restoration():
    trace = FailureRecoveryEngine.simulate_recovery(FailureScenarioType.AGENT_TOOL_CRASH)
    assert trace.recovered_successfully is True
    assert trace.scenario == FailureScenarioType.AGENT_TOOL_CRASH
    assert any("CONTEXT_STORE_CHECKPOINT" in s.stage for s in trace.steps)
    assert any("DISCOVERY_COMPLETED" in str(s.details) for s in trace.steps)

def test_lost_webhook_reconciliation():
    trace = FailureRecoveryEngine.simulate_recovery(FailureScenarioType.WEBHOOK_LOST)
    assert trace.recovered_successfully is True
    assert trace.scenario == FailureScenarioType.WEBHOOK_LOST
    assert any("CONFIRMED" in str(s.details) for s in trace.steps)
    assert any("BlueDart" in str(s.details) for s in trace.steps)
