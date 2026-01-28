
import os
import sys
import json
from unittest.mock import MagicMock, patch

# Adjust path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Mock dependencies to avoid import errors
from unittest.mock import MagicMock, patch
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["chromadb"] = MagicMock()
sys.modules["mcp"] = MagicMock()
sys.modules["mcp.client.stdio"] = MagicMock()
sys.modules["litellm"] = MagicMock() # Mock litellm at module level too just in case
sys.modules["celery"] = MagicMock()
sys.modules["backend.app.celery_app"] = MagicMock()

# We need to mock litellm before importing tool_creator if we want to avoid real calls
# But we can also patch it after import or during the test function.
from backend.app.services.tool_creator import ToolCreator
from backend.app.services.orchestrator import JarvisOrchestrator

# Sample Tool Code
SAMPLE_TOOL_CODE = """
def multiply_numbers(a: int, b: int) -> int:
    "Multiplies two numbers."
    return a * b
"""

SAMPLE_TEST_CODE = """
import unittest
from tool_module import multiply_numbers

class TestMultiply(unittest.TestCase):
    def test_multiply(self):
        self.assertEqual(multiply_numbers(2, 3), 6)
        print("TEST_PASSED")

if __name__ == '__main__':
    unittest.main()
"""

def mock_completion(*args, **kwargs):
    prompt = kwargs.get('messages', [])[0]['content']
    mock_resp = MagicMock()
    
    if "Python developer" in prompt: # Tool Generation
        mock_resp.choices = [MagicMock(message=MagicMock(content=SAMPLE_TOOL_CODE))]
    else: # Test Generation
        mock_resp.choices = [MagicMock(message=MagicMock(content=SAMPLE_TEST_CODE))]
        
    return mock_resp

def test_tool_creation_pipeline():
    print("--- Starting Tool Creation Pipeline Verification ---")
    
    # 1. Initialize ToolCreator
    creator = ToolCreator()
    
    # 2. Patch completion to avoid LLM calls
    with patch('backend.app.services.tool_creator.completion', side_effect=mock_completion):
        
        tool_name = "multiply_numbers"
        print(f"1. Requesting creation of '{tool_name}'...")
        
        # 3. Call create_tool
        result = creator.create_tool(tool_name, "Multiply two numbers")
        
        print(f"2. Result: {json.dumps(result, indent=2)}")
        
        if isinstance(result, dict) and result.get("status") == "success":
            print("SUCCESS: Tool successfully validated and saved.")
            file_path = result["file_path"]
            
            # 4. Verify File Exists
            if os.path.exists(file_path):
                print(f"SUCCESS: File exists at {file_path}")
            else:
                print(f"ERROR: File not found at {file_path}")
                return
            
            # 5. Verify Dynamic Loading (Orchestrator Logic)
            print("3. Testing Dynamic Loading...")
            orchestrator = JarvisOrchestrator() # mocks will likely be needed for __init__ if it connects to DBs
            
            # Monkey patch the DB connections in orchestrator to avoid errors
            orchestrator.episodic_memory = MagicMock()
            orchestrator.semantic_memory = MagicMock()
            orchestrator.chat_service = MagicMock()
            orchestrator.start = MagicMock()
            
            # Try to load
            loaded = orchestrator._load_dynamic_tool(tool_name, file_path)
            if loaded:
                print("SUCCESS: Tool loaded dynamically.")
                
                # 6. Execute Loaded Tool
                if tool_name in orchestrator.dynamic_tools:
                    func = orchestrator.dynamic_tools[tool_name]
                    exec_result = func(2, 3)
                    print(f"4. Execution Result (2*3): {exec_result}")
                    if exec_result == 6:
                         print("SUCCESS: Tool execution correct.")
                    else:
                         print("ERROR: Tool execution failed logic.")
                else:
                    print("ERROR: Tool not found in dynamic_tools registry.")
            else:
                print("ERROR: Failed to load tool dynamically.")
                
        else:
            print("ERROR: Tool creation failed.")
            print(result)

if __name__ == "__main__":
    test_tool_creation_pipeline()
