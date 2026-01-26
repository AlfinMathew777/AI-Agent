
import requests
import time

def check_backend():
    url = "http://127.0.0.1:8002/health"
    print(f"Checking {url}...")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Text: {response.text}")
        if response.status_code == 200:
            print("SUCCESS: Backend is reachable.")
        else:
            print("FAILURE: Backend returned non-200 code.")
    except Exception as e:
        print(f"FAILURE: Could not connect to backend. Error: {e}")
        print("\nPossible causes:")
        print("1. Backend server is NOT running.")
        print("2. Backend crashed on startup.")
        print("3. Backend is running on a different port (e.g. 8001).")

if __name__ == "__main__":
    check_backend()
