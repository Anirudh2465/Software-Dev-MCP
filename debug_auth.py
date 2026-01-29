import requests
import sys

BASE_URL = "http://localhost:8001"

def debug_auth():
    username = "debug_user_1"
    password = "password123"
    
    print(f"1. Signup {username}...")
    try:
        r = requests.post(f"{BASE_URL}/auth/signup", json={"username": username, "password": password})
        print(f"Signup Status: {r.status_code}")
        print(f"Signup Response: {r.text}")
    except Exception as e:
        print(f"Signup Request Failed: {e}")
        return

    print(f"\n2. Login {username}...")
    try:
        r = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": password})
        print(f"Login Status: {r.status_code}")
        print(f"Login Response: {r.text}")
        
        if r.status_code == 200:
            token = r.json()["access_token"]
            print(f"\n3. Check /auth/me...")
            r_me = requests.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {token}"})
            print(f"Me Status: {r_me.status_code}")
            print(f"Me Response: {r_me.text}")
            
            print(f"\n4. Check /memory/Work...")
            r_mem = requests.get(f"{BASE_URL}/memory/Work", headers={"Authorization": f"Bearer {token}"})
            print(f"Memory Status: {r_mem.status_code}")
            print(f"Memory Response: {r_mem.text}")
            
    except Exception as e:
        print(f"Login Request Failed: {e}")

if __name__ == "__main__":
    debug_auth()
