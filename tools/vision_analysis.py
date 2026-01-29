import base64
import os
from pathlib import Path
from litellm import completion

def analyze_image(image_path: str, prompt: str = "Describe this image in detail."):
    """
    Analyzes an image using a local vision-capable LLM.
    
    Args:
        image_path (str): Absolute path to the image file.
        prompt (str): The question or instruction for the vision model.
        
    Returns:
        str: The model's description or answer.
    """
    path = Path(image_path)
    if not path.exists():
        return f"Error: Image file not found at {image_path}"
        
    try:
        # 1. Read and Encode Image
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        # 2. Construct Payload for Vision Model (OpenAI-compatible format)
        # Most local servers (LM Studio, Ollama) support this format for vision models.
        image_url = f"data:image/jpeg;base64,{encoded_string}"
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    }
                ]
            }
        ]
        
        # 3. Call LLM
        # We rely on the environment variables already set for the main agent
        # or default to localhost.
        print(f"DEBUG: Sending image analysis request for {path.name}...")
        
        response = completion(
            model=os.getenv("LLM_MODEL", "openai/local-model"),
            api_base=os.getenv("LLM_API_BASE", "http://localhost:1234/v1"),
            api_key=os.getenv("LLM_API_KEY", "lm-studio"),
            messages=messages,
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error analyzing image: {e}. (Ensure your local model supports Vision!)"
