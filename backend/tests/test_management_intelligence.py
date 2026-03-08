"""
Management Intelligence API Tests

Tests for the Management AI dashboard endpoints:
- GET /api/management/metrics - Real-time KPIs (manager/admin only)
- POST /api/management/chat - AI chat with live data (manager/admin only)
- GET /api/management/insights - AI-generated business insights (manager/admin only)
- GET /api/management/examples - Example queries

Role-based access control tests:
- Admin: Full access
- Manager: Full access  
- Front Desk: 403 Forbidden
- Guest: 403 Forbidden
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials by role
CREDENTIALS = {
    "admin": {"email": "admin@hotel.com", "password": "admin123"},
    "manager": {"email": "manager@hotel.com", "password": "manager123"},
    "front_desk": {"email": "frontdesk@hotel.com", "password": "frontdesk123"},
    "guest": {"email": "guest@hotel.com", "password": "guest123"}
}


def get_token(role: str) -> str:
    """Helper to get auth token for a specific role."""
    creds = CREDENTIALS[role]
    # Login uses OAuth2PasswordRequestForm (form-urlencoded)
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": creds["email"], "password": creds["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    print(f"Login failed for {role}: {response.status_code} - {response.text}")
    return None


def get_auth_headers(role: str) -> dict:
    """Get authorization headers for a role."""
    token = get_token(role)
    if token:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    return {"Content-Type": "application/json"}


class TestManagementMetricsEndpoint:
    """Tests for GET /api/management/metrics"""
    
    def test_metrics_admin_access_success(self):
        """Admin should have full access to metrics endpoint."""
        headers = get_auth_headers("admin")
        response = requests.get(f"{BASE_URL}/api/management/metrics", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify required KPI fields exist
        assert "occupancy_rate" in data, "Missing occupancy_rate"
        assert "revenue_today" in data, "Missing revenue_today"
        assert "active_reservations" in data, "Missing active_reservations"
        assert "available_rooms" in data, "Missing available_rooms"
        assert "room_types" in data, "Missing room_types"
        assert "upcoming_arrivals" in data, "Missing upcoming_arrivals"
        
        # Verify data types
        assert isinstance(data["occupancy_rate"], (int, float)), "occupancy_rate should be numeric"
        assert isinstance(data["revenue_today"], (int, float)), "revenue_today should be numeric"
        assert isinstance(data["active_reservations"], int), "active_reservations should be int"
        assert isinstance(data["available_rooms"], int), "available_rooms should be int"
        
        print(f"Metrics retrieved: Occupancy={data['occupancy_rate']}%, Revenue=${data['revenue_today']}, Active={data['active_reservations']}, Available={data['available_rooms']}")
    
    def test_metrics_manager_access_success(self):
        """Manager should have full access to metrics endpoint."""
        headers = get_auth_headers("manager")
        response = requests.get(f"{BASE_URL}/api/management/metrics", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "occupancy_rate" in data
        assert "revenue_today" in data
        print(f"Manager access verified: Occupancy={data['occupancy_rate']}%")
    
    def test_metrics_front_desk_forbidden(self):
        """Front desk role should get 403 for metrics endpoint."""
        headers = get_auth_headers("front_desk")
        response = requests.get(f"{BASE_URL}/api/management/metrics", headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("Front desk correctly denied access to metrics (403)")
    
    def test_metrics_guest_forbidden(self):
        """Guest role should get 403 for metrics endpoint."""
        headers = get_auth_headers("guest")
        response = requests.get(f"{BASE_URL}/api/management/metrics", headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("Guest correctly denied access to metrics (403)")
    
    def test_metrics_unauthenticated_fails(self):
        """Unauthenticated request should fail."""
        response = requests.get(f"{BASE_URL}/api/management/metrics")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Unauthenticated access correctly blocked")


class TestManagementChatEndpoint:
    """Tests for POST /api/management/chat"""
    
    def test_chat_admin_access_success(self):
        """Admin should be able to use chat endpoint."""
        headers = get_auth_headers("admin")
        response = requests.post(
            f"{BASE_URL}/api/management/chat",
            headers=headers,
            json={"message": "What is the current occupancy rate?", "include_metrics": False}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "answer" in data, "Missing answer field"
        assert "timestamp" in data, "Missing timestamp field"
        assert len(data["answer"]) > 0, "Answer should not be empty"
        
        print(f"Chat response received, answer length: {len(data['answer'])} chars")
    
    def test_chat_manager_access_success(self):
        """Manager should be able to use chat endpoint."""
        headers = get_auth_headers("manager")
        response = requests.post(
            f"{BASE_URL}/api/management/chat",
            headers=headers,
            json={"message": "Show me today's revenue summary", "include_metrics": True}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "answer" in data
        # When include_metrics=True, should have metrics
        if "metrics" in data and data["metrics"]:
            assert "revenue_today" in data["metrics"]
            print(f"Chat with metrics: Revenue=${data['metrics']['revenue_today']}")
        print("Manager chat access verified")
    
    def test_chat_front_desk_forbidden(self):
        """Front desk role should get 403 for chat endpoint."""
        headers = get_auth_headers("front_desk")
        response = requests.post(
            f"{BASE_URL}/api/management/chat",
            headers=headers,
            json={"message": "What is occupancy?", "include_metrics": False}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("Front desk correctly denied access to chat (403)")
    
    def test_chat_guest_forbidden(self):
        """Guest role should get 403 for chat endpoint."""
        headers = get_auth_headers("guest")
        response = requests.post(
            f"{BASE_URL}/api/management/chat",
            headers=headers,
            json={"message": "What is revenue?", "include_metrics": False}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("Guest correctly denied access to chat (403)")
    
    def test_chat_empty_message_fails(self):
        """Empty message should return 400."""
        headers = get_auth_headers("admin")
        response = requests.post(
            f"{BASE_URL}/api/management/chat",
            headers=headers,
            json={"message": "", "include_metrics": False}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("Empty message correctly rejected (400)")
    
    def test_chat_whitespace_message_fails(self):
        """Whitespace-only message should return 400."""
        headers = get_auth_headers("admin")
        response = requests.post(
            f"{BASE_URL}/api/management/chat",
            headers=headers,
            json={"message": "   ", "include_metrics": False}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("Whitespace message correctly rejected (400)")


class TestManagementInsightsEndpoint:
    """Tests for GET /api/management/insights"""
    
    def test_insights_admin_access_success(self):
        """Admin should have access to insights endpoint."""
        headers = get_auth_headers("admin")
        response = requests.get(f"{BASE_URL}/api/management/insights", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "insights" in data, "Missing insights field"
        assert "metrics_summary" in data, "Missing metrics_summary field"
        assert "generated_at" in data, "Missing generated_at field"
        
        # Verify insights structure
        assert isinstance(data["insights"], list), "insights should be a list"
        
        # Verify metrics_summary structure
        summary = data["metrics_summary"]
        assert "occupancy_rate" in summary, "Missing occupancy_rate in summary"
        assert "active_reservations" in summary, "Missing active_reservations in summary"
        
        print(f"Insights retrieved: {len(data['insights'])} insights, Occupancy={summary['occupancy_rate']}%")
        
        # Print insight types for debugging
        for insight in data["insights"]:
            print(f"  - {insight.get('type', 'unknown')}: {insight.get('title', 'No title')}")
    
    def test_insights_manager_access_success(self):
        """Manager should have access to insights endpoint."""
        headers = get_auth_headers("manager")
        response = requests.get(f"{BASE_URL}/api/management/insights", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("Manager insights access verified")
    
    def test_insights_front_desk_forbidden(self):
        """Front desk should get 403 for insights endpoint."""
        headers = get_auth_headers("front_desk")
        response = requests.get(f"{BASE_URL}/api/management/insights", headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("Front desk correctly denied access to insights (403)")
    
    def test_insights_guest_forbidden(self):
        """Guest should get 403 for insights endpoint."""
        headers = get_auth_headers("guest")
        response = requests.get(f"{BASE_URL}/api/management/insights", headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("Guest correctly denied access to insights (403)")


class TestManagementExamplesEndpoint:
    """Tests for GET /api/management/examples"""
    
    def test_examples_admin_access(self):
        """Admin should have access to examples endpoint."""
        headers = get_auth_headers("admin")
        response = requests.get(f"{BASE_URL}/api/management/examples", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "examples" in data, "Missing examples field"
        assert isinstance(data["examples"], list), "examples should be a list"
        assert len(data["examples"]) > 0, "Should have at least one example"
        
        # Verify example structure
        example = data["examples"][0]
        assert "text" in example, "Example missing text field"
        assert "category" in example, "Example missing category field"
        
        print(f"Examples retrieved: {len(data['examples'])} examples")


class TestMetricsDataValidation:
    """Tests to verify metrics contain expected real-time data."""
    
    def test_metrics_room_types_structure(self):
        """Verify room_types array has correct structure."""
        headers = get_auth_headers("admin")
        response = requests.get(f"{BASE_URL}/api/management/metrics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        room_types = data.get("room_types", [])
        assert isinstance(room_types, list), "room_types should be a list"
        
        if room_types:
            rt = room_types[0]
            assert "room_type" in rt, "Missing room_type field"
            assert "total" in rt, "Missing total field"
            assert "available" in rt, "Missing available field"
            room_info = [f"{r.get('room_type')}: {r.get('available')}/{r.get('total')}" for r in room_types]
            print(f"Room types: {room_info}")
    
    def test_metrics_upcoming_arrivals_structure(self):
        """Verify upcoming_arrivals array has correct structure."""
        headers = get_auth_headers("admin")
        response = requests.get(f"{BASE_URL}/api/management/metrics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        arrivals = data.get("upcoming_arrivals", [])
        assert isinstance(arrivals, list), "upcoming_arrivals should be a list"
        
        if arrivals:
            arr = arrivals[0]
            assert "guest_name" in arr, "Missing guest_name field"
            assert "room_number" in arr, "Missing room_number field"
            assert "check_in_date" in arr, "Missing check_in_date field"
            print(f"Upcoming arrivals: {len(arrivals)} guests")
        else:
            print("No upcoming arrivals in the next 3 days")
    
    def test_metrics_revenue_values(self):
        """Verify revenue values are non-negative."""
        headers = get_auth_headers("admin")
        response = requests.get(f"{BASE_URL}/api/management/metrics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("revenue_today", 0) >= 0, "revenue_today should be non-negative"
        assert data.get("revenue_week", 0) >= 0, "revenue_week should be non-negative"
        assert data.get("revenue_month", 0) >= 0, "revenue_month should be non-negative"
        
        print(f"Revenue: Today=${data['revenue_today']}, Week=${data['revenue_week']}, Month=${data['revenue_month']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
