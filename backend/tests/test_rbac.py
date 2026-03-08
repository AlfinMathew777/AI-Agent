"""
RBAC (Role-Based Access Control) Tests for A2A Hotel Platform

Tests the following:
- Login API returns correct role, allowed_pages, allowed_features for each role
- /auth/me endpoint returns correct permissions for authenticated user
- Role-based access control for various endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials for all 6 roles
TEST_CREDENTIALS = {
    "admin": {"email": "admin@hotel.com", "password": "admin123"},
    "manager": {"email": "manager@hotel.com", "password": "manager123"},
    "front_desk": {"email": "frontdesk@hotel.com", "password": "frontdesk123"},
    "housekeeping": {"email": "housekeeping@hotel.com", "password": "housekeeping123"},
    "restaurant": {"email": "restaurant@hotel.com", "password": "restaurant123"},
    "guest": {"email": "guest@hotel.com", "password": "guest123"},
}

# Expected permissions per role from roles.py
EXPECTED_PERMISSIONS = {
    "admin": {
        "pages": ["a2a", "chat", "admin", "operations", "analytics", "staff_chat", "management"],
        "features": ["manage_users", "manage_rooms", "view_analytics", "view_operations", 
                     "staff_ai", "management_ai", "booking", "file_upload", "system_config"],
        "is_staff": True,
        "is_management": True,
    },
    "manager": {
        "pages": ["a2a", "chat", "operations", "analytics", "staff_chat", "management"],
        "features": ["view_analytics", "view_operations", "staff_ai", "management_ai", "booking"],
        "is_staff": True,
        "is_management": True,
    },
    "front_desk": {
        "pages": ["a2a", "chat", "operations", "staff_chat"],
        "features": ["view_operations", "staff_ai", "booking", "check_in_out", "reservations"],
        "is_staff": True,
        "is_management": False,
    },
    "housekeeping": {
        "pages": ["operations", "staff_chat"],
        "features": ["view_operations", "staff_ai", "room_cleaning", "housekeeping_tasks"],
        "is_staff": True,
        "is_management": False,
    },
    "restaurant": {
        "pages": ["operations", "staff_chat"],
        "features": ["view_operations", "staff_ai", "food_orders", "menu_management"],
        "is_staff": True,
        "is_management": False,
    },
    "guest": {
        "pages": ["chat"],
        "features": ["booking", "guest_services"],
        "is_staff": False,
        "is_management": False,
    },
}


@pytest.fixture
def client():
    """Shared requests session."""
    session = requests.Session()
    return session


def get_auth_token(client, role):
    """Helper to get auth token for a specific role."""
    creds = TEST_CREDENTIALS[role]
    resp = client.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": creds["email"], "password": creds["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if resp.status_code == 200:
        return resp.json()
    return None


class TestLoginReturnsCorrectPermissions:
    """Test that login API returns correct role, allowed_pages, allowed_features for each role."""
    
    def test_admin_login_permissions(self, client):
        """Admin login should return admin role with all pages and features."""
        data = get_auth_token(client, "admin")
        assert data is not None, "Admin login failed"
        
        assert data["role"] == "admin", f"Expected role 'admin', got '{data['role']}'"
        assert "allowed_pages" in data, "Missing allowed_pages in response"
        assert "allowed_features" in data, "Missing allowed_features in response"
        
        # Verify admin has all expected pages
        for page in EXPECTED_PERMISSIONS["admin"]["pages"]:
            assert page in data["allowed_pages"], f"Admin missing page: {page}"
        
        print(f"[OK] Admin login: role={data['role']}, pages={data['allowed_pages']}")
    
    def test_manager_login_permissions(self, client):
        """Manager login should return manager role without admin page."""
        data = get_auth_token(client, "manager")
        assert data is not None, "Manager login failed"
        
        assert data["role"] == "manager", f"Expected role 'manager', got '{data['role']}'"
        
        # Manager should NOT have admin page
        assert "admin" not in data["allowed_pages"], "Manager should not have admin page"
        
        # Manager should have these pages
        for page in ["a2a", "chat", "operations", "analytics", "staff_chat", "management"]:
            assert page in data["allowed_pages"], f"Manager missing page: {page}"
        
        print(f"[OK] Manager login: role={data['role']}, pages={data['allowed_pages']}")
    
    def test_front_desk_login_permissions(self, client):
        """Front desk login should return front_desk role with limited pages."""
        data = get_auth_token(client, "front_desk")
        assert data is not None, "Front desk login failed"
        
        assert data["role"] == "front_desk", f"Expected role 'front_desk', got '{data['role']}'"
        
        # Front desk should have these pages
        for page in ["a2a", "chat", "operations", "staff_chat"]:
            assert page in data["allowed_pages"], f"Front desk missing page: {page}"
        
        # Front desk should NOT have these pages
        for page in ["admin", "analytics", "management"]:
            assert page not in data["allowed_pages"], f"Front desk should not have page: {page}"
        
        print(f"[OK] Front desk login: role={data['role']}, pages={data['allowed_pages']}")
    
    def test_housekeeping_login_permissions(self, client):
        """Housekeeping login should return housekeeping role with minimal pages."""
        data = get_auth_token(client, "housekeeping")
        assert data is not None, "Housekeeping login failed"
        
        assert data["role"] == "housekeeping", f"Expected role 'housekeeping', got '{data['role']}'"
        
        # Housekeeping should have these pages
        for page in ["operations", "staff_chat"]:
            assert page in data["allowed_pages"], f"Housekeeping missing page: {page}"
        
        # Housekeeping should NOT have these pages
        for page in ["admin", "analytics", "management", "a2a", "chat"]:
            assert page not in data["allowed_pages"], f"Housekeeping should not have page: {page}"
        
        print(f"[OK] Housekeeping login: role={data['role']}, pages={data['allowed_pages']}")
    
    def test_restaurant_login_permissions(self, client):
        """Restaurant login should return restaurant role with minimal pages."""
        data = get_auth_token(client, "restaurant")
        assert data is not None, "Restaurant login failed"
        
        assert data["role"] == "restaurant", f"Expected role 'restaurant', got '{data['role']}'"
        
        # Restaurant should have these pages
        for page in ["operations", "staff_chat"]:
            assert page in data["allowed_pages"], f"Restaurant missing page: {page}"
        
        # Restaurant should NOT have these pages
        for page in ["admin", "analytics", "management", "a2a", "chat"]:
            assert page not in data["allowed_pages"], f"Restaurant should not have page: {page}"
        
        print(f"[OK] Restaurant login: role={data['role']}, pages={data['allowed_pages']}")
    
    def test_guest_login_permissions(self, client):
        """Guest login should return guest role with only chat page."""
        data = get_auth_token(client, "guest")
        assert data is not None, "Guest login failed"
        
        assert data["role"] == "guest", f"Expected role 'guest', got '{data['role']}'"
        
        # Guest should ONLY have chat page
        assert "chat" in data["allowed_pages"], "Guest missing chat page"
        assert len(data["allowed_pages"]) == 1, f"Guest should only have 1 page, got {data['allowed_pages']}"
        
        print(f"[OK] Guest login: role={data['role']}, pages={data['allowed_pages']}")


class TestAuthMeEndpoint:
    """Test that /api/auth/me returns correct permissions for authenticated user."""
    
    @pytest.mark.parametrize("role", ["admin", "manager", "front_desk", "housekeeping", "restaurant", "guest"])
    def test_auth_me_returns_correct_permissions(self, client, role):
        """Test /auth/me endpoint returns correct permissions for each role."""
        # First login to get token
        login_data = get_auth_token(client, role)
        assert login_data is not None, f"{role} login failed"
        
        token = login_data.get("access_token")
        assert token, f"No access_token for {role}"
        
        # Call /auth/me with the token
        resp = client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert resp.status_code == 200, f"/auth/me failed for {role}: {resp.status_code} {resp.text}"
        
        data = resp.json()
        expected = EXPECTED_PERMISSIONS[role]
        
        # Check role matches
        assert data["role"] == role, f"Expected role '{role}', got '{data['role']}'"
        
        # Check is_staff flag
        assert data["is_staff"] == expected["is_staff"], \
            f"is_staff mismatch for {role}: expected {expected['is_staff']}, got {data['is_staff']}"
        
        # Check is_management flag
        assert data["is_management"] == expected["is_management"], \
            f"is_management mismatch for {role}: expected {expected['is_management']}, got {data['is_management']}"
        
        # Check pages match
        for page in expected["pages"]:
            assert page in data["allowed_pages"], f"{role} missing page in /auth/me: {page}"
        
        print(f"[OK] /auth/me for {role}: is_staff={data['is_staff']}, is_management={data['is_management']}, pages={data['allowed_pages']}")


class TestAllRolesCanLogin:
    """Test that all 6 test accounts can successfully login."""
    
    @pytest.mark.parametrize("role", ["admin", "manager", "front_desk", "housekeeping", "restaurant", "guest"])
    def test_role_can_login(self, client, role):
        """Test that each role's test account can login successfully."""
        creds = TEST_CREDENTIALS[role]
        resp = client.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": creds["email"], "password": creds["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert resp.status_code == 200, f"Login failed for {role}: {resp.status_code} {resp.text}"
        
        data = resp.json()
        assert "access_token" in data, f"No access_token for {role}"
        assert data["role"] == role, f"Wrong role for {role}: expected '{role}', got '{data['role']}'"
        assert data["email"] == creds["email"], f"Wrong email for {role}"
        
        print(f"[OK] {role} login successful: email={data['email']}")


class TestLoginResponseStructure:
    """Test that login response has all expected fields."""
    
    def test_login_response_has_all_fields(self, client):
        """Test that login response includes all required RBAC fields."""
        data = get_auth_token(client, "admin")
        assert data is not None, "Admin login failed"
        
        # Required fields for RBAC
        required_fields = [
            "access_token",
            "token_type",
            "role",
            "tenant_id",
            "user_id",
            "email",
            "full_name",
            "allowed_pages",
            "allowed_features",
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field in login response: {field}"
        
        assert data["token_type"] == "bearer", f"Expected token_type 'bearer', got '{data['token_type']}'"
        assert isinstance(data["allowed_pages"], list), "allowed_pages should be a list"
        assert isinstance(data["allowed_features"], list), "allowed_features should be a list"
        
        print(f"[OK] Login response has all required fields: {list(data.keys())}")


class TestInvalidLogin:
    """Test invalid login scenarios."""
    
    def test_invalid_credentials_rejected(self, client):
        """Test that invalid credentials are rejected."""
        resp = client.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": "invalid@hotel.com", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert resp.status_code in [401, 403], f"Expected 401/403 for invalid credentials, got {resp.status_code}"
        print(f"[OK] Invalid credentials correctly rejected with status {resp.status_code}")
    
    def test_wrong_password_rejected(self, client):
        """Test that wrong password is rejected."""
        resp = client.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": "admin@hotel.com", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert resp.status_code in [401, 403], f"Expected 401/403 for wrong password, got {resp.status_code}"
        print(f"[OK] Wrong password correctly rejected with status {resp.status_code}")


class TestAuthMeWithoutToken:
    """Test /auth/me endpoint without authentication."""
    
    def test_auth_me_requires_authentication(self, client):
        """Test that /auth/me requires a valid token."""
        resp = client.get(f"{BASE_URL}/api/auth/me")
        assert resp.status_code == 401, f"Expected 401 without token, got {resp.status_code}"
        print(f"[OK] /auth/me correctly requires authentication")
    
    def test_auth_me_rejects_invalid_token(self, client):
        """Test that /auth/me rejects invalid tokens."""
        resp = client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert resp.status_code == 401, f"Expected 401 for invalid token, got {resp.status_code}"
        print(f"[OK] /auth/me correctly rejects invalid token")
