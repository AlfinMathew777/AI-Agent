import json
import sys
import time
from datetime import date, timedelta
import requests

# Safe printing on Windows terminals
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8002"

def post(path: str, payload: dict, timeout=20):
    url = BASE + path
    r = requests.post(url, json=payload, timeout=timeout)
    return r

def get(path: str, timeout=10):
    url = BASE + path
    r = requests.get(url, timeout=timeout)
    return r

def assert_ok(r, label):
    if not r.ok:
        raise RuntimeError(f"{label} FAILED: HTTP {r.status_code} {r.text[:300]}")
    return r

def pretty(obj):
    return json.dumps(obj, indent=2, ensure_ascii=True)

def main():
    print("Phase 4.1 verification starting (ASCII-safe)...")

    # 0) Health check
    r = get("/health")
    assert_ok(r, "HEALTH")
    print("HEALTH OK:", r.text)

    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # 1) READ tool: availability check (should not require confirmation)
    payload1 = {
        "audience": "guest",
        "question": f"Check if standard room is available on {tomorrow}",
        "session_id": "t_read_1"
    }
    r = post("/ask/agent", payload1)
    assert_ok(r, "READ_TOOL")
    data = r.json()
    print("READ_TOOL response:", pretty(data))

    if data.get("status") == "needs_confirmation":
        raise RuntimeError("READ_TOOL unexpectedly requires confirmation (should be READ).")

    # 2) WRITE tool: booking should require confirmation
    payload2 = {
        "audience": "guest",
        "question": f"Book a standard room for John Doe on {tomorrow}",
        "session_id": "t_write_1"
    }
    r = post("/ask/agent", payload2)
    assert_ok(r, "WRITE_TOOL_REQUEST")
    data = r.json()
    print("WRITE_TOOL_REQUEST response:", pretty(data))

    if data.get("status") != "needs_confirmation":
        raise RuntimeError("WRITE_TOOL_REQUEST did not return needs_confirmation.")

    action_id = data.get("action_id") or data.get("actionId")
    if not action_id:
        raise RuntimeError("No action_id returned in needs_confirmation response.")

    # 3) Confirm booking
    payload3 = {"action_id": action_id, "confirm": True}
    r = post("/ask/agent/confirm", payload3)
    assert_ok(r, "CONFIRM_BOOKING")
    data = r.json()
    print("CONFIRM_BOOKING response:", pretty(data))

    # 4) Availability check again (should be consistent)
    payload4 = {
        "audience": "guest",
        "question": f"Check if standard room is available on {tomorrow}",
        "session_id": "t_read_2"
    }
    r = post("/ask/agent", payload4)
    assert_ok(r, "READ_TOOL_AFTER_BOOKING")
    data = r.json()
    print("READ_TOOL_AFTER_BOOKING response:", pretty(data))

    # 5) Cancel flow quick check (create new pending action, then cancel)
    payload5 = {
        "audience": "guest",
        "question": f"Book a standard room for Jane Smith on {tomorrow}",
        "session_id": "t_write_2"
    }
    r = post("/ask/agent", payload5)
    assert_ok(r, "WRITE_TOOL_REQUEST_2")
    data = r.json()
    print("WRITE_TOOL_REQUEST_2 response:", pretty(data))

    if data.get("status") != "needs_confirmation":
        raise RuntimeError("WRITE_TOOL_REQUEST_2 did not return needs_confirmation.")

    action_id2 = data.get("action_id") or data.get("actionId")
    if not action_id2:
        raise RuntimeError("No action_id returned in second needs_confirmation response.")

    payload6 = {"action_id": action_id2, "confirm": False}
    r = post("/ask/agent/confirm", payload6)
    assert_ok(r, "CANCEL_BOOKING")
    data = r.json()
    print("CANCEL_BOOKING response:", pretty(data))

    print("\nALL TESTS PASSED (Phase 4.1).")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend.")
        print("Make sure uvicorn is running on http://127.0.0.1:8002 (see Step 1).")
        sys.exit(2)
    except Exception as e:
        print("ERROR:", str(e))
        sys.exit(1)
