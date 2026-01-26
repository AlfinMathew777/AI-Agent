import requests
import json

url = "http://127.0.0.1:8000/ask/guest"
payload = {
    "question": "Where can I find the best scallop pie?"
}

print("Sending request...")
try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
