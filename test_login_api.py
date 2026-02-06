
import requests
import json

BASE_URL = "http://127.0.0.1:8011"

def test_register_and_login():
    email = "debug_user_123@example.com"
    password = "password123"
    
    print(f"Attempting to register new user: {email}")
    
    # Register
    reg_payload = {
        "email": email,
        "password": password,
        "full_name": "Debug User",
        "role": "owner"
    }
    
    try:
        # Note: In Login.jsx, registration uses /api/auth/register (proxied to /auth/register)
        # We are hitting backend directly, so /auth/register
        reg_resp = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
        
        if reg_resp.status_code == 200:
            print("Registration successful!")
            print(reg_resp.json())
        elif reg_resp.status_code == 400 and "already registered" in reg_resp.text:
             print("User already registered. Proceeding to login.")
        else:
            print(f"Registration failed: {reg_resp.status_code} - {reg_resp.text}")
            return

        # Login
        print("\nAttempting login...")
        login_data = {
            "username": email,
            "password": password
        }
        
        login_resp = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        
        if login_resp.status_code == 200:
            print("Login successful!")
            print(login_resp.json())
        else:
            print(f"Login failed: {login_resp.status_code} - {login_resp.text}")
            
    except Exception as e:
        print(f"Exception during request: {e}")

if __name__ == "__main__":
    test_register_and_login()
