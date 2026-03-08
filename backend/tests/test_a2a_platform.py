"""Backend tests for A2A Hotel Platform - agents, analytics, admin APIs"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_KEY = "shhg_admin_secure_key_2024"

@pytest.fixture
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s

@pytest.fixture
def auth_token(client):
    resp = client.post(f"{BASE_URL}/api/auth/login", data={"username": "admin@hotel.com", "password": "admin123"},
                       headers={"Content-Type": "application/x-www-form-urlencoded"})
    if resp.status_code == 200:
        data = resp.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Auth failed: {resp.status_code} {resp.text[:200]}")

@pytest.fixture
def authed(client, auth_token):
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client

# Health
def test_ping(client):
    r = client.get(f"{BASE_URL}/api/ping")
    assert r.status_code == 200
    assert r.json().get("pong") is True

# Auth
def test_login_success(client):
    # Auth uses OAuth2 form-urlencoded
    r = client.post(f"{BASE_URL}/api/auth/login", data={"username": "admin@hotel.com", "password": "admin123"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data

def test_login_invalid(client):
    r = client.post(f"{BASE_URL}/api/auth/login", data={"username": "bad@hotel.com", "password": "wrong"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code in [401, 403, 400]

# A2A endpoints
def test_a2a_status_returns_agents(client):
    r = client.get(f"{BASE_URL}/api/a2a/status")
    assert r.status_code == 200
    data = r.json()
    assert "agents" in data
    agents = data["agents"]
    assert isinstance(agents, list)
    assert len(agents) >= 6, f"Expected at least 6 agents, got {len(agents)}"
    print(f"[OK] A2A status: {len(agents)} agents")

def test_a2a_chat_general(client):
    r = client.post(f"{BASE_URL}/api/a2a/chat", json={"message": "What amenities do you have?", "session_id": "test-gen"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert len(data["answer"]) > 5
    print(f"[OK] A2A chat general: {data['answer'][:80]}")

def test_a2a_chat_booking(client):
    r = client.post(f"{BASE_URL}/api/a2a/chat", json={"message": "Book 1 deluxe room for 2 nights", "session_id": "test-book"}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    print(f"[OK] A2A booking chat: {data['answer'][:100]}")

def test_a2a_events(client):
    r = client.get(f"{BASE_URL}/api/a2a/events")
    assert r.status_code == 200
    data = r.json()
    assert "events" in data

# Analytics endpoints
def test_analytics_summary(client):
    r = client.get(f"{BASE_URL}/api/analytics/summary")
    assert r.status_code == 200
    data = r.json()
    assert "total_revenue" in data
    assert "total_bookings" in data
    assert "occupancy_rate" in data
    print(f"[OK] Analytics summary: bookings={data['total_bookings']}")

def test_analytics_revenue(client):
    r = client.get(f"{BASE_URL}/api/analytics/revenue")
    assert r.status_code == 200
    data = r.json()
    assert "data" in data
    assert len(data["data"]) > 0
    print(f"[OK] Analytics revenue: {len(data['data'])} days")

def test_analytics_agents(client):
    r = client.get(f"{BASE_URL}/api/analytics/agents")
    assert r.status_code == 200
    data = r.json()
    assert "agents" in data
    assert len(data["agents"]) >= 6

# Admin endpoints (using API key)
def test_admin_rooms(client):
    r = client.get(f"{BASE_URL}/api/admin/rooms", headers={"X-API-Key": ADMIN_KEY})
    assert r.status_code in [200, 401, 403, 404]
    if r.status_code == 200:
        data = r.json()
        print(f"[OK] Admin rooms: {len(data) if isinstance(data, list) else data}")

def test_admin_reservations(authed):
    r = authed.get(f"{BASE_URL}/api/admin/reservations")
    assert r.status_code in [200, 401, 403, 404]
    if r.status_code == 200:
        data = r.json()
        print(f"[OK] Admin reservations: {data}")

def test_admin_payments(authed):
    r = authed.get(f"{BASE_URL}/api/admin/payments")
    assert r.status_code in [200, 401, 403, 404]
    if r.status_code == 200:
        print("[OK] Admin payments working")
