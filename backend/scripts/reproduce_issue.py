import requests
import json

url = "http://127.0.0.1:8001/ask/guest"
payload = {"question": "Hello"}

try:
    print(f"Testing POST to {url}...")
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print("Response Text:")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
