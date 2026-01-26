
import requests
import json

def debug_http():
    url = "http://localhost:8002/ask/guest"
    payload = {"question": "Is the pool open?"}
    print(f"Sending POST to {url}...")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        try:
            data = response.json()
            print("Response JSON:", json.dumps(data, indent=2))
        except:
            print("Response Text:", response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    debug_http()
