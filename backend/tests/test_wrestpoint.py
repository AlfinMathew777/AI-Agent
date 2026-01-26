import requests
import json

url = "http://127.0.0.1:8000/ask/guest"

questions = [
    "Is there a dance competition on today?",
    "What is the dress code for The Point?",
    "Where can I get a cocktail?"
]

print("Testing Wrest Point Knowledge...")
for q in questions:
    payload = {"question": q}
    try:
        response = requests.post(url, json=payload)
        print(f"\nQ: {q}")
        print(f"A: {json.loads(response.text)['answer']}")
    except Exception as e:
        print(f"Error: {e}")
