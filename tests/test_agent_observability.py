"""
Test Suite for 11. Agent Observability (Operational Waterfall Trace & Telemetry KPIs)
"""
import pytest
from backend.agent.observability import (
    AgentObservabilityEngine, ExecutionMetricSummary, TimestampedExecutionEvent
)

def test_observability_metrics_kpi_block():
    trace = AgentObservabilityEngine.get_latest_session_trace()
    m = trace.metrics

    # Verify exact user metric requirements
    assert m.steps == 11
    assert m.tool_calls == 17
    assert m.latency_sec == 2.8
    assert m.total_tokens == 4823
    assert m.estimated_cost_usd == 0.04
    assert m.retries == 1
    assert m.policy_violations == 0

def test_exact_timestamped_events_sequence():
    trace = AgentObservabilityEngine.get_latest_session_trace()
    events = trace.events
    assert len(events) >= 9

    # 12:31:02 Intent Agent ✓ Requirements extracted
    assert events[0].timestamp == "12:31:02"
    assert events[0].agent_or_component == "Intent Agent"
    assert events[0].status_icon == "✓"
    assert "Requirements extracted" in events[0].summary

    # 12:31:03 Planner ✓ Created shopping plan
    assert events[1].timestamp == "12:31:03"
    assert events[1].agent_or_component == "Planner"
    assert events[1].status_icon == "✓"
    assert "Created shopping plan" in events[1].summary

    # 12:31:03 Merchant A ✓ 17 products
    assert events[2].timestamp == "12:31:03"
    assert events[2].agent_or_component == "Merchant A"
    assert "17 products" in events[2].summary

    # 12:31:04 Merchant B ✓ 23 products
    assert events[3].timestamp == "12:31:04"
    assert events[3].agent_or_component == "Merchant B"
    assert "23 products" in events[3].summary

    # 12:31:05 Ranking Agent ✓ Top 5 selected
    assert events[4].timestamp == "12:31:05"
    assert events[4].agent_or_component == "Ranking Agent"
    assert "Top 5 selected" in events[4].summary

    # 12:31:06 Policy Engine ✓ Purchase permitted
    assert events[5].timestamp == "12:31:06"
    assert events[5].agent_or_component == "Policy Engine"
    assert "Purchase permitted" in events[5].summary

    # 12:31:07 Cart Agent ✓ Cart created
    assert events[6].timestamp == "12:31:07"
    assert events[6].agent_or_component == "Cart Agent"
    assert "Cart created" in events[6].summary

    # 12:31:08 Checkout Agent ✓ Final total calculated
    assert events[7].timestamp == "12:31:08"
    assert events[7].agent_or_component == "Checkout Agent"
    assert "Final total calculated" in events[7].summary

    # 12:31:08 Authorization ⚠ User approval required
    assert events[8].timestamp == "12:31:08"
    assert events[8].agent_or_component == "Authorization"
    assert events[8].status_icon == "⚠"
    assert "User approval required" in events[8].summary

def test_flamegraph_spans():
    trace = AgentObservabilityEngine.get_latest_session_trace()
    spans = trace.flamegraph_spans
    assert len(spans) >= 8
    assert any("Intent" in s["agent"] for s in spans)
    assert any("Ranking" in s["agent"] for s in spans)
