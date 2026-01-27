from litellm import completion
import os
import sys

models_to_test = [
    "gemini/gemini-2.0-flash-exp",
    "gemini/gemini-1.5-flash",
    "gemini/gemini-1.5-flash-001",
    "gemini/gemini-1.5-pro",
    "gemini/gemini-pro"
]

def test_model(model_name):
    print(f"Testing {model_name}...", flush=True)
    try:
        response = completion(
            model=model_name,
            messages=[{"role": "user", "content": "Hello"}],
            api_key=os.getenv("GEMINI_API_KEY")
        )
        print(f"SUCCESS: {model_name}", flush=True)
        return True
    except Exception as e:
        print(f"FAILURE: {model_name} - {str(e)}", flush=True)
        return False

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not set")
        sys.exit(1)
        
    for model in models_to_test:
        if test_model(model):
            print(f"\nRecommended model: {model}")
            break
