import requests
import uuid
import json
import time

BASE_URL = "http://127.0.0.1:8002"

def test_read_action():
    print("\n--- TEST 1: Read Action (Check Availability) ---")
    url = f"{BASE_URL}/ask/agent"
    payload = {
        "audience": "guest",
        "question": "Check if standard room is available tomorrow",
        "session_id": str(uuid.uuid4())
    }
    
    try:
        res = requests.post(url, json=payload)
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(res.json(), indent=2)}")
    except Exception as e:
        print(f"Failed: {e}")

def test_write_action_flow():
    print("\n--- TEST 2: Write Action (Book Room) - Step 1: Request ---")
    url = f"{BASE_URL}/ask/agent"
    session_id = str(uuid.uuid4())
    
    payload = {
        "audience": "guest",
        "question": "Book a standard room for John Doe tomorrow",
        "session_id": session_id
    }
    
    try:
        res = requests.post(url, json=payload)
        data = res.json()
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get("status") == "needs_confirmation":
            print("\n--- TEST 3: Write Action (Book Room) - Step 2: Confirm ---")
            payload["confirm"] = True
            
            # Allow a small delay to simulate user thinking
            time.sleep(1)
            
            res_conf = requests.post(url, json=payload)
            print(f"Status: {res_conf.status_code}")
            print(f"Response: {json.dumps(res_conf.json(), indent=2)}")
            
        else:
            print("ERROR: Expected confirmation request, got execution!")

    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    # Wait for server to potentially reload
    print("Waiting 2s for server reload...")
    time.sleep(2)
    test_read_action()
    test_write_action_flow()
