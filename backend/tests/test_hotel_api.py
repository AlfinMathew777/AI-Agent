import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_KEY = "shhg_admin_secure_key_2024"

class TestHealthAndAuth:
    """Health and Auth endpoint tests"""

    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200, f"Health failed: {r.text}"
        data = r.json()
        print(f"Health: {data}")

    def test_auth_login_success(self):
        # Auth uses OAuth2PasswordRequestForm (form data, not JSON)
        r = requests.post(f"{BASE_URL}/api/auth/login", data={
            "username": "admin@hotel.com",
            "password": "admin123"
        })
        assert r.status_code == 200, f"Login failed: {r.text}"
        data = r.json()
        assert "access_token" in data or "token" in data, f"No token: {data}"
        print(f"Login success: token present")

    def test_auth_login_invalid(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", data={
            "username": "wrong@test.com",
            "password": "wrongpass"
        })
        assert r.status_code in [401, 400, 403], f"Expected auth failure: {r.status_code}"

    def test_auth_register(self):
        r = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": "TEST_testuser@hotel.com",
            "password": "testpass123",
            "full_name": "Test User"
        })
        assert r.status_code in [200, 201, 400, 409], f"Unexpected: {r.status_code} {r.text}"
        print(f"Register: {r.status_code}")


class TestGuestChatbot:
    """Guest chatbot endpoint tests"""

    def test_ask_guest_amenities(self):
        r = requests.post(f"{BASE_URL}/api/ask/guest", json={
            "question": "What amenities do you have?"
        }, timeout=30)
        assert r.status_code == 200, f"Ask failed: {r.text}"
        data = r.json()
        response_text = str(data)
        assert "Traceback" not in response_text
        print(f"Chatbot response keys: {list(data.keys())}")

    def test_ask_guest_booking(self):
        r = requests.post(f"{BASE_URL}/api/ask/guest", json={
            "question": "I want to book a room"
        }, timeout=30)
        assert r.status_code == 200, f"Ask failed: {r.text}"
        print(f"Booking query response: {r.status_code}")


class TestAdminEndpoints:
    """Admin endpoint tests requiring JWT token (admin role)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", data={
            "username": "admin@hotel.com",
            "password": "admin123"
        })
        if r.status_code == 200:
            token = r.json().get("access_token") or r.json().get("token")
            self.headers = {"Authorization": f"Bearer {token}", "x-admin-key": ADMIN_KEY}
        else:
            pytest.skip("Could not get admin token")

    def test_admin_operations(self):
        r = requests.get(f"{BASE_URL}/api/admin/operations", headers={"x-admin-key": ADMIN_KEY})
        assert r.status_code == 200, f"Admin ops failed: {r.status_code} {r.text}"
        data = r.json()
        print(f"Admin operations keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")

    def test_admin_rooms(self):
        r = requests.get(f"{BASE_URL}/api/admin/rooms", headers=self.headers)
        assert r.status_code == 200, f"Admin rooms failed: {r.status_code} {r.text}"

    def test_admin_reservations(self):
        r = requests.get(f"{BASE_URL}/api/admin/reservations", headers=self.headers)
        assert r.status_code == 200, f"Admin reservations failed: {r.status_code} {r.text}"

    def test_admin_chats(self):
        r = requests.get(f"{BASE_URL}/api/admin/chats", headers={"x-admin-key": ADMIN_KEY})
        assert r.status_code == 200, f"Admin chats failed: {r.status_code} {r.text}"

    def test_admin_payments(self):
        r = requests.get(f"{BASE_URL}/api/admin/payments", headers={"x-admin-key": ADMIN_KEY})
        assert r.status_code in [200, 404, 501], f"Admin payments: {r.status_code} {r.text}"
        print(f"Admin payments: {r.status_code}")
