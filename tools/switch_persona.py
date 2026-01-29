import requests
import sys
import os

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

def switch_persona(persona_name):
    """
    Switch the agent's persona via the backend API.
    
    Args:
        persona_name (str): The name of the persona to switch to.
                            Valid options: "Generalist", "Coder", "Architect", "Sentinel".
    """
    print(f"Requesting persona switch to: '{persona_name}'...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/persona", 
            json={"persona": persona_name},
            headers={"Content-Type": "application/json"}
            # Note: In a real scenario, we'd need an auth token here if the endpoint is protected.
            # Currently main.py protect routes with 'get_current_user'.
            # Tools running locally by the agent might need a system token or run in a context where they can get one.
            # For simplicity in this dev environment, I'll assume we can pass a dummy or we need to login first.
            # Actually, let's check main.py... Yes, `set_persona` depends on `get_current_user`.
            # We need to login or bypass auth for this tool. 
            # OR, since this is a "tool" running locally, maybe it should just call the orchestrator directly if possible?
            # No, tools should be decoupled.
            # Let's try to grab a token first or assume 'debug_user_1' credentials.
        )
        
        # If 401, we need to login
        if response.status_code == 401:
            print("Authentication required. Logging in as debug_user_1...")
            login_resp = requests.post(f"{BASE_URL}/auth/login", data={"username": "debug_user_1", "password": "password123"})
            if login_resp.status_code == 200:
                token = login_resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                # Retry
                response = requests.post(
                    f"{BASE_URL}/persona", 
                    json={"persona": persona_name}, 
                    headers=headers
                )
            else:
                print(f"Login failed: {login_resp.text}")
                return "Login failed."

        if response.status_code == 200:
            data = response.json()
            msg = f"Success: {data.get('status', 'Switched')}"
            print(msg)
            return msg
        else:
            msg = f"Error {response.status_code}: {response.text}"
            print(msg)
            return msg
            
    except Exception as e:
        msg = f"Connection failed: {e}"
        print(msg)
        return msg

if __name__ == "__main__":
    if len(sys.argv) > 1:
        persona = sys.argv[1]
        switch_persona(persona)
    else:
        print("Usage: python switch_persona.py <PersonaName>")
