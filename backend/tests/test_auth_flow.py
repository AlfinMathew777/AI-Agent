import requests
import uuid
import time

BASE_URL = "http://localhost:8002"

def test_auth_flow():
    # 1. Register a new user (New Tenant)
    email = f"test_owner_{uuid.uuid4().hex[:6]}@example.com"
    password = "securepassword123"
    
    print(f"\n[TEST] Registering user: {email}")
    reg_res = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Test Owner",
        "role": "owner"
    })
    
    if reg_res.status_code != 200:
        print(f"Registration Failed: {reg_res.text}")
        return
        
    user_data = reg_res.json()
    tenant_id = user_data["tenant_id"]
    print(f"✅ Registered. User ID: {user_data['id']}, Tenant ID: {tenant_id}")
    
    # 2. Login
    print(f"\n[TEST] Logging in...")
    login_res = requests.post(f"{BASE_URL}/auth/login", data={
        "username": email,
        "password": password
    })
    
    if login_res.status_code != 200:
        print(f"Login Failed: {login_res.text}")
        return
        
    token_data = login_res.json()
    token = token_data["access_token"]
    print(f"✅ Logged in. Token received.")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Test Protected Endpoint (Agent)
    print(f"\n[TEST] Accessing Protected Agent Endpoint...")
    agent_res = requests.post(f"{BASE_URL}/ask/agent", headers=headers, json={
        "audience": "guest",
        "question": "Hello, are you working?"
    })
    
    if agent_res.status_code == 200:
        print(f"✅ Agent Response: {agent_res.json().get('response', '')[:50]}...")
    else:
        print(f"❌ Agent Access Failed: {agent_res.text}")
        
    # 4. Test Tenant Isolation (Admin Stats)
    print(f"\n[TEST] Checking Admin Index Status (Should be empty/linked to new tenant)...")
    admin_res = requests.get(f"{BASE_URL}/admin/index/status", headers=headers)
    
    if admin_res.status_code == 200:
        stats = admin_res.json()
        print(f"✅ Admin Stats: {stats}")
        # Expect 0 docs for new tenant usually
        if stats["guest_docs"] == 0:
            print("   (Confirmed: New tenant starts with 0 docs)")
    else:
        print(f"❌ Admin Access Failed: {admin_res.text}")

    # 5. Authorization Failure Check
    print(f"\n[TEST] Testing Invalid Token...")
    bad_res = requests.get(f"{BASE_URL}/admin/index/status", headers={"Authorization": "Bearer badtoken"})
    if bad_res.status_code == 401:
        print(f"✅ Correctly rejected invalid token (401)")
    else:
        print(f"❌ Security Flaw: Accepted bad token? Code: {bad_res.status_code}")

if __name__ == "__main__":
    try:
        test_auth_flow()
    except Exception as e:
        print(f"Test crashed: {e}")
