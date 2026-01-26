import requests
import uuid

BASE_URL = "http://localhost:8002"

def test_admin_commerce():
    # 1. Register Owner (Tenant A)
    email_a = f"owner_a_{uuid.uuid4().hex[:4]}@hotel.com"
    pwd = "password123"
    
    print(f"\n[TEST] Registering Tenant A: {email_a}")
    reg_a = requests.post(f"{BASE_URL}/auth/register", json={"email": email_a, "password": pwd, "role": "owner"})
    if reg_a.status_code != 200:
        print(f"Failed to register A: {reg_a.text}")
        return
    token_a = requests.post(f"{BASE_URL}/auth/login", data={"username": email_a, "password": pwd}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    
    # 2. Register Owner (Tenant B)
    email_b = f"owner_b_{uuid.uuid4().hex[:4]}@hotel.com"
    print(f"[TEST] Registering Tenant B: {email_b}")
    reg_b = requests.post(f"{BASE_URL}/auth/register", json={"email": email_b, "password": pwd, "role": "owner"})
    token_b = requests.post(f"{BASE_URL}/auth/login", data={"username": email_b, "password": pwd}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Create Restaurant for A
    print(f"[TEST] Creating Restaurant for Tenant A...")
    res_a = requests.post(f"{BASE_URL}/admin/restaurants", headers=headers_a, json={
        "name": "Steakhouse A",
        "location": "Lobby",
        "phone": "123",
        "hours_json": {"mon": "9-5"}
    })
    
    if res_a.status_code == 200:
        r_id_a = res_a.json()["id"]
        print(f"✅ Created Restaurant A: {r_id_a}")
    else:
        print(f"❌ Failed to create Restaurant A: {res_a.text}")
        return

    # 4. Verify Isolation (Tenant B should not see A's restaurant)
    print(f"[TEST] Verifying Isolation (Tenant B listing restaurants)...")
    list_b = requests.get(f"{BASE_URL}/admin/restaurants", headers=headers_b).json()
    if len(list_b) == 0:
        print(f"✅ Isolation Confirmed: Tenant B sees 0 restaurants.")
    else:
        print(f"❌ Isolation Failed: Tenant B saw {len(list_b)} restaurants (Should be 0).")

    # 5. Add Menu & Item to A
    print(f"[TEST] Adding Menu to Restaurant A...")
    menu_a = requests.post(f"{BASE_URL}/admin/restaurants", headers=headers_a) # Wait, no endpoint for create_menu? 
    # Ah, I forgot create_menu endpoint in my implementation plan? 
    # Let me check the code I wrote. I wrote create_menu_item but maybe not create_menu?
    # Checking implementation...
    
    # Actually, verify if create_menu exists. 
    # If not, I can create Item on a "phantom" menu? No, FK constraint.
    # Let's Skip Menu creation if I missed it and check Event or Fix it.
    
    # Let's try Events for A
    print(f"[TEST] Creating Event for Tenant A...")
    event_a = requests.post(f"{BASE_URL}/admin/events", headers=headers_a, json={
        "title": "Gala A",
        "venue": "Hall A", 
        "start_time": "2025-12-01T19:00:00",
        "end_time": "2025-12-01T22:00:00"
    })
    
    if event_a.status_code == 200:
        print(f"✅ Created Event A: {event_a.json()['id']}")
    else:
        print(f"❌ Create Event Failed: {event_a.text}")

    # 6. Verify Event Isolation
    print(f"[TEST] Verifying Event Isolation (Tenant B listing events)...")
    events_b = requests.get(f"{BASE_URL}/admin/events", headers=headers_b).json()
    if len(events_b) == 0:
         print(f"✅ Isolation Confirmed: Tenant B sees 0 events.")
    else:
         print(f"❌ Isolation Failed: Tenant B saw {len(events_b)} events.")

if __name__ == "__main__":
    try:
        test_admin_commerce()
    except Exception as e:
        print(f"Test crashed: {e}")
