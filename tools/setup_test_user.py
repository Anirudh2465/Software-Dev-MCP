import requests
import os

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

def setup_user():
    username = "debug_user_1"
    password = "password123"
    
    print(f"Creating user {username}...")
    try:
        r = requests.post(f"{BASE_URL}/auth/signup", json={"username": username, "password": password})
        if r.status_code == 200:
            print("User created successfully.")
        elif r.status_code == 400 and "already registered" in r.text:
            print("User already exists.")
        else:
            print(f"Signup failed: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    setup_user()
