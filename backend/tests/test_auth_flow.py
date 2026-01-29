from fastapi.testclient import TestClient
from backend.app.main import app
import pytest

client = TestClient(app)

def test_auth_flow():
    # 1. Signup
    username = "testuser_verif"
    password = "password123"
    
    # Try signup
    response = client.post("/auth/signup", json={"username": username, "password": password})
    # If user exists from previous run, it might fail with 400, which is fine for this simple test script, 
    # but ideally we clean up. For now assuming new user or handling 400.
    if response.status_code == 400:
        print("User likely exists, proceeding to login.")
    else:
        assert response.status_code == 200
        assert response.json()["username"] == username

    # 2. Login
    response = client.post("/auth/login", data={"username": username, "password": password})
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    
    # 3. Access Protected Route (Me)
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == username
    
    # 4. Access Protected Route (Services) without token
    response = client.get("/history")
    assert response.status_code == 401

if __name__ == "__main__":
    test_auth_flow()
    print("Auth Flow Verified.")
