"""
Staff AI & Knowledge Base API Tests
Tests the staff chat and admin knowledge base management endpoints
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_KEY = "shhg_admin_secure_key_2024"

# Test credentials from PRD
TEST_USERS = {
    "admin": {"username": "admin@hotel.com", "password": "admin123"},
    "front_desk": {"username": "frontdesk@hotel.com", "password": "frontdesk123"},
    "housekeeping": {"username": "housekeeping@hotel.com", "password": "housekeeping123"},
    "guest": {"username": "guest@hotel.com", "password": "guest123"}
}


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    return session


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        data=TEST_USERS["admin"],
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def front_desk_token(api_client):
    """Get front_desk authentication token"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        data=TEST_USERS["front_desk"],
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Front desk login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def housekeeping_token(api_client):
    """Get housekeeping authentication token"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        data=TEST_USERS["housekeeping"],
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Housekeeping login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def guest_token(api_client):
    """Get guest authentication token"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        data=TEST_USERS["guest"],
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Guest login failed: {response.text}"
    return response.json()["access_token"]


class TestStaffChatAuthentication:
    """Test authentication/authorization for staff chat endpoint"""
    
    def test_staff_chat_requires_auth(self, api_client):
        """POST /api/staff/chat returns 401 for unauthenticated requests"""
        response = api_client.post(
            f"{BASE_URL}/api/staff/chat",
            json={"message": "What is check-out policy?"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "Could not validate credentials" in data.get("detail", "")
    
    def test_staff_chat_blocks_guest_role(self, api_client, guest_token):
        """POST /api/staff/chat returns 403 for guest role users"""
        response = api_client.post(
            f"{BASE_URL}/api/staff/chat",
            json={"message": "What is check-out policy?"},
            headers={"Authorization": f"Bearer {guest_token}"}
        )
        assert response.status_code == 403
        data = response.json()
        assert "Staff access required" in data.get("detail", "")
    
    def test_staff_context_requires_auth(self, api_client):
        """GET /api/staff/context returns 401 for unauthenticated requests"""
        response = api_client.get(f"{BASE_URL}/api/staff/context")
        assert response.status_code == 401


class TestStaffChatFunctionality:
    """Test staff chat AI responses for different roles"""
    
    def test_admin_staff_chat(self, api_client, admin_token):
        """POST /api/staff/chat returns AI response for admin role"""
        response = api_client.post(
            f"{BASE_URL}/api/staff/chat",
            json={"message": "What are the emergency procedures?"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "answer" in data
        assert "sources" in data
        assert "role_context" in data
        assert "chunks_used" in data
        assert "session_id" in data
        assert "timestamp" in data
        
        # Verify role context is Administrator
        assert data["role_context"] == "Administrator"
        assert len(data["answer"]) > 50  # Has substantial answer
        assert data["chunks_used"] > 0  # RAG retrieved chunks
    
    def test_front_desk_staff_chat(self, api_client, front_desk_token):
        """POST /api/staff/chat returns role-aware response for front_desk"""
        response = api_client.post(
            f"{BASE_URL}/api/staff/chat",
            json={"message": "How do I handle a guest complaint?"},
            headers={"Authorization": f"Bearer {front_desk_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify role context is Front Desk Staff
        assert data["role_context"] == "Front Desk Staff"
        assert len(data["answer"]) > 50
        assert "sources" in data
    
    def test_housekeeping_staff_chat(self, api_client, housekeeping_token):
        """POST /api/staff/chat returns role-aware response for housekeeping"""
        response = api_client.post(
            f"{BASE_URL}/api/staff/chat",
            json={"message": "What is the room cleaning checklist?"},
            headers={"Authorization": f"Bearer {housekeeping_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify role context is Housekeeping Staff
        assert data["role_context"] == "Housekeeping Staff"
        assert len(data["answer"]) > 50
        assert "sources" in data
    
    def test_staff_chat_empty_message_validation(self, api_client, admin_token):
        """POST /api/staff/chat returns 400 for empty message"""
        response = api_client.post(
            f"{BASE_URL}/api/staff/chat",
            json={"message": "   "},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400


class TestStaffContext:
    """Test staff context endpoint for different roles"""
    
    def test_admin_context(self, api_client, admin_token):
        """GET /api/staff/context returns correct context for admin"""
        response = api_client.get(
            f"{BASE_URL}/api/staff/context",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["role"] == "admin"
        assert data["title"] == "Administrator"
        assert "focus_areas" in data
        assert "example_questions" in data
        assert len(data["focus_areas"]) > 0
        assert len(data["example_questions"]) > 0
    
    def test_front_desk_context(self, api_client, front_desk_token):
        """GET /api/staff/context returns correct context for front_desk"""
        response = api_client.get(
            f"{BASE_URL}/api/staff/context",
            headers={"Authorization": f"Bearer {front_desk_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["role"] == "front_desk"
        assert data["title"] == "Front Desk Staff"
        assert "check-in and check-out procedures" in data["focus_areas"]
    
    def test_housekeeping_context(self, api_client, housekeeping_token):
        """GET /api/staff/context returns correct context for housekeeping"""
        response = api_client.get(
            f"{BASE_URL}/api/staff/context",
            headers={"Authorization": f"Bearer {housekeeping_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["role"] == "housekeeping"
        assert data["title"] == "Housekeeping Staff"
        assert "room cleaning standards" in data["focus_areas"]


class TestAdminKnowledgeBase:
    """Test admin knowledge base management endpoints"""
    
    def test_get_files_list(self, api_client, admin_token):
        """GET /api/admin/files returns list of uploaded KB files"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/files",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "x-admin-key": ADMIN_KEY
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have guest and staff keys
        assert "guest" in data
        assert "staff" in data
        
        # Staff should have the 3 SOP files
        assert isinstance(data["staff"], list)
        assert len(data["staff"]) >= 3
        assert "front_desk_sop.md" in data["staff"]
        assert "housekeeping_sop.md" in data["staff"]
        assert "restaurant_sop.md" in data["staff"]
    
    def test_get_index_status(self, api_client, admin_token):
        """GET /api/admin/index/status returns vector index statistics"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/index/status",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "x-admin-key": ADMIN_KEY
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have document counts
        assert "guest_docs" in data
        assert "staff_docs" in data
        assert "last_reindex_time" in data
        
        # Staff docs should be > 0 (72 vectors indexed)
        assert data["staff_docs"] > 0
    
    def test_reindex_knowledge_base(self, api_client, admin_token):
        """POST /api/admin/reindex reindexes the knowledge base"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/reindex",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "x-admin-key": ADMIN_KEY
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "files_processed" in data
        assert "chunks_added" in data
        assert data["files_processed"] >= 3  # At least 3 SOP files
        assert data["chunks_added"] > 0


class TestStaffExamplesEndpoint:
    """Test staff examples endpoint"""
    
    def test_get_examples_admin(self, api_client, admin_token):
        """GET /api/staff/examples returns example questions for admin"""
        response = api_client.get(
            f"{BASE_URL}/api/staff/examples",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["role"] == "admin"
        assert "examples" in data
        assert len(data["examples"]) > 0


class TestStaffRolesEndpoint:
    """Test staff roles public endpoint"""
    
    def test_get_available_roles(self, api_client):
        """GET /api/staff/roles returns all available staff roles"""
        response = api_client.get(f"{BASE_URL}/api/staff/roles")
        assert response.status_code == 200
        data = response.json()
        
        assert "roles" in data
        roles = data["roles"]
        
        # Should have 5 staff roles
        role_names = [r["role"] for r in roles]
        assert "front_desk" in role_names
        assert "housekeeping" in role_names
        assert "restaurant" in role_names
        assert "manager" in role_names
        assert "admin" in role_names


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
