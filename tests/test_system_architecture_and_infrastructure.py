"""
Test Suite for 13. System Architecture & Supporting Infrastructure (PostgreSQL, Redis, pgvector, OTel, Langfuse, Docker, CI/CD)
"""
import os
import pytest
from backend.infrastructure.telemetry_langfuse import InfrastructureManager, SupportingInfrastructureReport

def test_infrastructure_manager_services_count_and_status():
    report = InfrastructureManager.get_infrastructure_status()
    assert len(report.services) == 7
    
    expected_services = [
        "PostgreSQL 16",
        "Redis 7.2",
        "pgvector",
        "OpenTelemetry Collector",
        "Langfuse",
        "Docker Engine",
        "GitHub Actions"
    ]

    service_names = [s.service_name for s in report.services]
    for exp in expected_services:
        assert exp in service_names

    for s in report.services:
        assert s.status == "ONLINE"
        assert s.latency_ms > 0.0

def test_docker_and_ci_configuration_files():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    dockerfile_path = os.path.join(base_dir, "Dockerfile")
    docker_compose_path = os.path.join(base_dir, "docker-compose.yml")
    ci_workflow_path = os.path.join(base_dir, ".github", "workflows", "ci.yml")

    assert os.path.exists(dockerfile_path), "Dockerfile must exist"
    assert os.path.exists(docker_compose_path), "docker-compose.yml must exist"
    assert os.path.exists(ci_workflow_path), "CI workflow must exist"

    with open(docker_compose_path, "r", encoding="utf-8") as f:
        compose_content = f.read()
        assert "pgvector" in compose_content
        assert "redis" in compose_content
        assert "otel-collector" in compose_content
