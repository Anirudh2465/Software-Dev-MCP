import unittest
from unittest.mock import patch, MagicMock
import os
import shutil
from tool_creator import ToolCreator

class TestToolCreation(unittest.TestCase):
    def setUp(self):
        self.creator = ToolCreator()
        # Ensure clean state
        if os.path.exists("tools/test_reverse.py"):
            os.remove("tools/test_reverse.py")

    def test_pipeline_with_docker(self):
        print("\n--- Testing Tool Creation Pipeline ---")
        
        # MOCK LLM Responses so we don't depend on actual API availability or quality
        mock_response_code = MagicMock()
        mock_response_code.choices[0].message.content = """
def test_reverse(input_str):
    return input_str[::-1]
"""
        
        mock_response_test = MagicMock()
        # The test code that ToolCreator will run inside Docker
        # Note: ToolCreator expects to find 'tool_module'
        mock_response_test.choices[0].message.content = """
import unittest
from tool_module import test_reverse

class TestReverse(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(test_reverse("hello"), "olleh")

if __name__ == "__main__":
    unittest.main()
"""
        # Patch the completion call AND subprocess.run
        with patch('tool_creator.completion', side_effect=[mock_response_code, mock_response_test]), \
             patch('subprocess.run') as mock_subproc:
            
            # Setup mock for subprocess.run to simulate Docker SUCCESS
            mock_subproc.return_value = MagicMock(returncode=0, stdout="TEST_PASSED", stderr="")
            
            tool_name = "test_reverse"
            desc = "Reverses a string"
            
            print(f"Initiating create_tool for '{tool_name}'...")
            result = self.creator.create_tool(tool_name, desc)
            
            print(f"Result: {result}")
            
            # Assertions
            self.assertTrue("saved to" in result)
            self.assertTrue(os.path.exists(f"tools/{tool_name}.py"))
            
            # Check content
            with open(f"tools/{tool_name}.py", "r") as f:
                content = f.read()
                self.assertIn("return input_str[::-1]", content)
                
            print("--- Pipeline Test Passed (Mocked Docker) ---")
            
            # Verify Docker was actually called
            mock_subproc.assert_called()
            args, _ = mock_subproc.call_args
            self.assertEqual(args[0][0], "docker")

    def tearDown(self):
        # Cleanup
        if os.path.exists("tools/test_reverse.py"):
            os.remove("tools/test_reverse.py")

if __name__ == "__main__":
    unittest.main()
