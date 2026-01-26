import requests
import json

try:
    response = requests.get("http://127.0.0.1:8002/admin/analytics")
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
