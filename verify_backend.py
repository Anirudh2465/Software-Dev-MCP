import requests

try:
    # Check Health
    print("Checking Health...")
    r = requests.get("http://localhost:8000/health", timeout=2)
    print(f"Health Status: {r.status_code}")
    print(f"Health Body: {r.text}")

    # Check CORS (OPTIONS)
    print("\nChecking CORS (OPTIONS /chat)...")
    r = requests.options(
        "http://localhost:8000/chat",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        },
        timeout=2
    )
    print(f"OPTIONS Status: {r.status_code}")
    print(f"Allow-Origin: {r.headers.get('access-control-allow-origin')}")

except Exception as e:
    print(f"Connection Failed: {e}")
