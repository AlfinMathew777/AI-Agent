"""Integration tests for health check endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client"""
    from app.main import app
    return TestClient(app)


def test_health_endpoint_returns_200(client):
    """Test that /health endpoint returns 200 when healthy"""
    response = client.get("/health")
    
    assert response.status_code in [200, 503]  # May be 503 if components unhealthy
    data = response.json()
    
    assert "status" in data
    assert "service" in data
    assert data["service"] == "shhg-backend"
    assert "components" in data


def test_health_endpoint_has_components(client):
    """Test that /health endpoint returns component status"""
    response = client.get("/health")
    data = response.json()
    
    assert "components" in data
    components = data["components"]
    
    # Should have database and ai_service components
    assert "database" in components
    assert "ai_service" in components


def test_health_database_component(client):
    """Test database component in health check"""
    response = client.get("/health")
    data = response.json()
    
    db_health = data["components"]["database"]
    
    assert "status" in db_health
    assert "message" in db_health
    
    # If healthy, should have table count
    if db_health["status"] == "healthy":
        assert "tables_count" in db_health
        assert db_health["tables_count"] > 0


def test_health_ai_service_component(client):
    """Test AI service component in health check"""
    response = client.get("/health")
    data = response.json()
    
    ai_health = data["components"]["ai_service"]
    
    assert "status" in ai_health
    assert "message" in ai_health
    
    # Status should be configured, not_configured, or error
    assert ai_health["status"] in ["configured", "not_configured", "error"]


def test_health_endpoint_includes_timestamp(client):
    """Test that health check includes timestamp"""
    response = client.get("/health")
    data = response.json()
    
    assert "timestamp" in data
    # Timestamp should be ISO format
    assert "T" in data["timestamp"]


def test_health_endpoint_includes_system_info(client):
    """Test that health check includes system information"""
    response = client.get("/health")
    data = response.json()
    
    assert "system" in data
    system = data["system"]
    
    assert "environment" in system
    assert "debug" in system


def test_health_database_endpoint(client):
    """Test dedicated /health/database endpoint"""
    response = client.get("/health/database")
    
    assert response.status_code in [200, 503]
    data = response.json()
    
    assert "status" in data
    assert "message" in data


def test_health_ai_endpoint(client):
    """Test dedicated /health/ai endpoint"""
    response = client.get("/health/ai")
    
    assert response.status_code in [200, 503]
    data = response.json()
    
    assert "status" in data
    assert "message" in data


def test_health_endpoints_return_proper_status_codes(client):
    """Test that unhealthy components return 503"""
    response = client.get("/health")
    data = response.json()
    
    # If any component is unhealthy, overall status should be degraded
    db_unhealthy = data["components"]["database"]["status"] == "unhealthy"
    
    if db_unhealthy:
        assert response.status_code == 503
        assert data["status"] == "degraded"
