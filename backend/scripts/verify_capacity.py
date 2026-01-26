import requests
import json
import sys

# Safe printing
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8002"

try:
    print("Verifying Capacity Logic...")
    payload = {
        "audience": "guest",
        "question": "Check if standard room is available tomorrow",
        "session_id": "test_capacity"
    }
    resp = requests.post(f"{BASE_URL}/ask/agent", json=payload)
    data = resp.json()
    
    print("Response Status:", getattr(resp, 'status_code', 'Unknown'))
    print("Body:", json.dumps(data, indent=2))
    
    answer = data.get("answer", "")
    if "Booked:" in answer:
        print("[PASS] SUCCESS: Found 'Booked: X/Y' info in response.")
    else:
        print("[FAIL] FAILURE: Missing capacity info in response.")

except Exception as e:
    print(f"[ERROR] {e}")
