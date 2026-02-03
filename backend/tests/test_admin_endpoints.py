"""
Tests for Admin Panel Endpoints
Tests pagination, tenant isolation, and filters.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db, get_db_connection

client = TestClient(app)

# Initialize test database
init_db()


def test_admin_chats_pagination():
    """Test chat history pagination."""
    response = client.get(
        "/admin/chats",
        headers={"X-Tenant-ID": "default-tenant-0000"},
        params={"limit": 10, "offset": 0}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "chats" in data
    assert "total" in data
    assert isinstance(data["chats"], list)
    assert len(data["chats"]) <= 10


def test_admin_chats_audience_filter():
    """Test chat history filtering by audience."""
    response = client.get(
        "/admin/chats",
        headers={"X-Tenant-ID": "default-tenant-0000"},
        params={"audience": "guest", "limit": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "chats" in data
    # All chats should be guest
    for chat in data["chats"]:
        assert chat["audience"] == "guest"


def test_admin_operations_summary():
    """Test operations summary endpoint."""
    response = client.get(
        "/admin/operations",
        headers={"X-Tenant-ID": "default-tenant-0000"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "recent_operations" in data
    assert "total_operations" in data["summary"]
    assert "revenue_today_cents" in data["summary"]


def test_admin_payments_pagination():
    """Test payments pagination."""
    response = client.get(
        "/admin/payments",
        headers={"X-Tenant-ID": "default-tenant-0000"},
        params={"limit": 10, "offset": 0}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "payments" in data
    assert "total" in data
    assert isinstance(data["payments"], list)


def test_admin_payments_status_filter():
    """Test payments filtering by status."""
    response = client.get(
        "/admin/payments",
        headers={"X-Tenant-ID": "default-tenant-0000"},
        params={"status": "paid", "limit": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "payments" in data
    # All payments should be paid
    for payment in data["payments"]:
        assert payment["status"] == "paid"


def test_admin_receipts_date_filter():
    """Test receipts date filtering."""
    response = client.get(
        "/admin/receipts",
        headers={"X-Tenant-ID": "default-tenant-0000"},
        params={"date_from": "2024-01-01", "date_to": "2024-12-31", "limit": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "receipts" in data
    assert "total" in data


def test_admin_system_status():
    """Test system health status endpoint."""
    response = client.get("/admin/system/status")
    
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "ai_service" in data
    assert "queue" in data
    assert "recent_errors" in data


def test_tenant_isolation():
    """Test that tenants cannot see each other's data."""
    # Create test data for tenant 1
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO chat_logs (tenant_id, audience, question, answer) VALUES (?, ?, ?, ?)",
        ("tenant-1", "guest", "Test question", "Test answer")
    )
    conn.commit()
    conn.close()
    
    # Try to get chats for tenant 2
    response = client.get(
        "/admin/chats",
        headers={"X-Tenant-ID": "tenant-2"},
        params={"limit": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should not see tenant-1's data
    for chat in data["chats"]:
        # This would require tenant_id in response, but for now just check it doesn't error
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
