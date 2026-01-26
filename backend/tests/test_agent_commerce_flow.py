import requests
import uuid
import json

BASE_URL = "http://localhost:8002"

def test_agent_commerce_flow():
    # 1. Register a new tenant/user to test isolation
    email = f"guest_comm_{uuid.uuid4().hex[:4]}@hotel.com"
    pwd = "password123"
    
    print(f"\n[TEST] Registering User: {email}")
    reg = requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": pwd, "role": "owner", "full_name": "Commerce Tester"})
    if reg.status_code != 200:
        print(f"❌ Registration Failed: {reg.text}")
        return
    
    token = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": pwd}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Seed Data for THIS tenant (Admin API)
    # Because listing restaurants might be empty for new tenant unless we create one.
    print(f"[TEST] Seeding Restaurant for this tenant...")
    res_create = requests.post(f"{BASE_URL}/admin/restaurants", headers=headers, json={
        "name": "Test Bistro", "location": "Lobby", "phone": "555", "hours_json": {}
    })
    r_id = res_create.json()["id"]

    # 3. Ask Agent: "List restaurants" (READ Tool)
    print(f"[TEST] Agent: 'What restaurants do you have?'")
    ask_read = requests.post(f"{BASE_URL}/ask/agent", headers=headers, json={
        "audience": "guest", "question": "What restaurants do you have?"
    })
    # Normal answer comes in 'answer'
    print(f"   -> Response: {ask_read.json().get('answer', 'No Answer')[:100]}...")
    
    # 4. Ask Agent: "Reserve a table" (WRITE Tool)
    # This should trigger confirmation.
    print(f"[TEST] Agent: 'Reserve a table at Test Bistro for tonight'")
    ask_write = requests.post(f"{BASE_URL}/ask/agent", headers=headers, json={
        "audience": "guest", 
        "question": f"Reserve a table at {r_id} for tonight at 7pm for 2 people"
    })
    
    resp_write = ask_write.json()
    
    if resp_write.get("status") == "needs_confirmation":
        print(f"✅ Correctly requested confirmation.")
        action_id = resp_write.get("action_id")
        print(f"   -> Action ID: {action_id}")
        
        # 5. Confirm the action
        print(f"[TEST] Confirming Action...")
        conf_res = requests.post(f"{BASE_URL}/ask/agent/confirm", headers=headers, json={
            "action_id": action_id, "confirm": True
        })
        
        if conf_res.status_code == 200:
            final_resp = conf_res.json()
            # Confirmation result comes in 'answer'
            print(f"✅ Confirmation Response: {final_resp.get('answer')}")
        else:
            print(f"❌ Confirmation Failed: {conf_res.text}")
            
    else:
        print(f"❌ Expected confirmation, got: {resp_write}")

    # 6. Verify Reservation in DB? (Or via tool)
    # Let's check availability again?
    # Or rely on the "Reservation Confirmed!" message above.

if __name__ == "__main__":
    try:
        test_agent_commerce_flow()
    except Exception as e:
        print(f"Test crashed: {e}")
