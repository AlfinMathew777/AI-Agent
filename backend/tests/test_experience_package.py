import requests
import uuid
import json

BASE_URL = "http://localhost:8002"

def test_experience_package():
    # 1. Setup Tenant/User
    email = f"pkg_user_{uuid.uuid4().hex[:4]}@hotel.com"
    pwd = "password123"
    print(f"\n[TEST] Registering: {email}")
    requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": pwd, "role": "owner"})
    token = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": pwd}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Seed Data (So we have options)
    # Restaurant
    res = requests.post(f"{BASE_URL}/admin/restaurants", headers=headers, json={
        "name": "Golden Grill", "location": "Roof", "phone": "1", "hours_json": {}
    }).json()
    r_name = res["name"]
    print(f"[TEST] Created Rest: {r_name}")
    
    # Event
    evt = requests.post(f"{BASE_URL}/admin/events", headers=headers, json={
        "title": "Neon Concert", "venue": "Hall", "start_time": "2026-06-01T20:00:00", "end_time": "2026-06-01T23:00:00", "status": "scheduled"
    }).json()
    # Add tickets (via raw SQL or just assume default capacity logic works? Ah, service needs ticket types in DB)
    # We do not have admin endpoint for tickets in Task 2. 
    # But seed script added them. 
    # Actually, Commerce Service's `buy_event_tickets` checks `event_tickets` table.
    # The Admin Event Create API *does not* create tickets. It just creates event.
    # We need to manually add tickets or rely on Seeded data if we used default tenant (but we are in isolated tenant).
    # **Fix**: Helper to add tickets? Or mock tool?
    # I'll use `check_event_availability` mock behavior if I implemented it loosely?
    # No, `check_event_availability` queries DB.
    # I should add a ticket via direct DB insert or just rely on a "Soft Mock" in the test?
    # OR, switch to Default Tenant! And use "Azure Horizon Grill" and "Jazz Night".
    # Yes, much easier.
    
    # SWITCH TO DEFAULT TENANT (Simulation)
    # Actually, default tenant is easiest for "Seeded" data.
    # But user asked for "Multi-tenant isolation must apply".
    # I should verify on *new* tenant.
    # I will stick to new tenant but I need to insert a ticket.
    # Can I use `sqlite3` directly on the file? Yes.
    
    # 2b. Inject Ticket for tenant
    import sqlite3
    # from app.core.config import DB_PATH <-- Removed to avoid import error
    DB_PATH = r"C:\PROJECT AI\ai-hotel-assistant\backend\hotel.db"

    # Direct DB Insert
    conn = sqlite3.connect(DB_PATH)
    t_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO event_tickets (id, tenant_id, event_id, ticket_type, price, capacity, sold_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (t_id, res["tenant_id"], evt["id"], "General", 50.0, 100, 0)
    )
    conn.commit()
    conn.close()
    print(f"[TEST] Injected Ticket for {evt['title']}")

    # 3. Explore Phase
    print(f"\n[TEST] 1. Explore Request: 'Plan a night... dinner + show'")
    q1 = "Plan a night for 2: dinner + show + room"
    resp1 = requests.post(f"{BASE_URL}/ask/agent", headers=headers, json={
        "audience": "guest", "question": q1
    }).json()
    
    print(f"Status: {resp1.get('status')}")
    if resp1.get("status") == "needs_input":
        print("✅ Correctly returned needs_input.")
        print(f"Summary: {resp1.get('answer')[:50]}...")
    else:
        print(f"❌ Failed Explore: {resp1}")
        return

    # 4. Commit Phase (Selection)
    print(f"\n[TEST] 2. Select: '{r_name} and {evt['title']}'")
    q2 = f"I want {r_name} and {evt['title']}"
    resp2 = requests.post(f"{BASE_URL}/ask/agent", headers=headers, json={
        "audience": "guest", "question": q2, "session_id": resp1["session_id"] # Must reuse session
    }).json()
    
    # Expect Needs Confirmation (Step 1: Reserve)
    if resp2.get("status") == "needs_confirmation":
        print(f"✅ Confirmation 1 (Reserve Table): {resp2['proposed_action']['tool']}")
        act_id = resp2["action_id"]
        
        # 5. Confirm 1
        print(f"\n[TEST] 3. Confirming Reservation...")
        resp3 = requests.post(f"{BASE_URL}/ask/agent/confirm", headers=headers, json={
            "action_id": act_id, "confirm": True
        }).json()
        
        # Expect Needs Confirmation (Step 2: Tickets) -- Or success if multi-step flow continues automatically?
        # Runner logic: `_execute_loop` -> `update_plan_status(pending)` -> return `needs_confirmation`
        # Upon resume (`execute_confirmed_action`), it calls `_execute_loop` again.
        # It should handle the next step.
        
        if resp3.get("status") == "needs_confirmation":
             print(f"✅ Confirmation 2 (Buy Tickets): {resp3['proposed_action']['tool']}")
             act_id_2 = resp3["action_id"]
             
             # 6. Confirm 2
             print(f"\n[TEST] 4. Confirming Tickets...")
             resp4 = requests.post(f"{BASE_URL}/ask/agent/confirm", headers=headers, json={
                "action_id": act_id_2, "confirm": True
             }).json()
             
             if resp4.get("status") == "needs_confirmation":
                  print(f"✅ Confirmation 3 (Book Room): {resp4['proposed_action']['tool']}")
                  act_id_3 = resp4["action_id"]
                  
                  # 7. Confirm 3
                  print(f"\n[TEST] 5. Confirming Room...")
                  resp5 = requests.post(f"{BASE_URL}/ask/agent/confirm", headers=headers, json={
                    "action_id": act_id_3, "confirm": True
                  }).json()
                  
                  print(f"Final Status: {resp5.get('status')}")
                  print(f"Final Answer: {resp5.get('answer')[:100]}")
             else:
                  print(f"Stopped early at step 3? {resp4}")

        else:
             print(f"Stopped early at step 2? {resp3}")
            
    else:
        print(f"❌ Failed Commit: {resp2}")

if __name__ == "__main__":
    try:
        test_experience_package()
    except Exception as e:
        print(f"Test crashed: {e}")
