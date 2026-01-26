import requests

try:
    print("Sending request...")
    res = requests.post("http://127.0.0.1:8000/ask/guest", json={"question": "Is the casino open?"}, timeout=10)
    print("Status:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print("Error:", e)
