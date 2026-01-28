import os
import json
import subprocess
import time
from litellm import completion
from pathlib import Path

# Paths relative to this file: .../backend/app/services/tool_creator.py
# We want tools to be in .../jarvis/tools/
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TOOLS_DIR = BASE_DIR / "tools"
TOOL_DEFINITIONS_FILE = BASE_DIR / "tool_definitions.json"

class ToolCreator:
    def __init__(self, model=None, api_base=None, api_key=None):
        self.model = model or os.getenv("LLM_MODEL", "openai/local-model")
        self.api_base = api_base or os.getenv("LLM_API_BASE", "http://localhost:1234/v1")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "lm-studio")
        
        if not os.path.exists(TOOLS_DIR):
            os.makedirs(TOOLS_DIR)
            
        if not os.path.exists(TOOL_DEFINITIONS_FILE):
             with open(TOOL_DEFINITIONS_FILE, "w") as f:
                 json.dump([], f)

    def generate_tool_code(self, tool_name, description, functionality_guidelines):
        """
        Generates Python code for a tool and a corresponding test script using the LLM.
        """
        # Prompt for Tool Code
        tool_prompt = f"""
        You are an expert Python developer. Create a single-file Python script for a tool named '{tool_name}'.
        
        [Process Description]
        {description}
        
        [Guidelines]
        {functionality_guidelines}
        
        [Requirements]
        1. structure it as a standalone function named '{tool_name}'.
        2. The function should take primitive types as arguments (str, int, float, bool) unless specified otherwise.
        3. Return the result as a string or a JSON-serializable dictionary.
        4. Include standard library imports ONLY. If external packages are ABSOLUTELY necessary, list them in a comment at the top like: # REQUIREMENTS: package1, package2
        5. DO NOT include any execution block (if __name__ == "__main__") in the tool code itself, just the function definition.
        6. Output ONLY the python code. No markdown formatting.
        """
        
        print(f"DEBUG: Generating code for {tool_name}...")
        try:
            response = completion(
                model=self.model,
                api_base=self.api_base,
                api_key=self.api_key,
                messages=[{"role": "user", "content": tool_prompt}]
            )
            tool_code = response.choices[0].message.content.strip()
            # Cleanup markdown if present
            if tool_code.startswith("```python"):
                tool_code = tool_code.split("```python")[1]
            if tool_code.endswith("```"):
                tool_code = tool_code.rsplit("```", 1)[0]
            tool_code = tool_code.strip()
            
        except Exception as e:
            return None, None, f"LLM generation failed: {e}"

        # Prompt for Test Code
        test_prompt = f"""
        You are a QA engineer. Write a Python test script to verify the following function:
        
        [Function Code]
        {tool_code}
        
        [Instructions]
        1. Import the function from 'tool_module' (we will rename the file dynamically).
        2. Call the function '{tool_name}' with typical inputs based on the description: "{description}".
        3. Assert the output is correct.
        4. If assertions fail, raise an Exception.
        5. If success, print "TEST_PASSED".
        6. Output ONLY the python code. No markdown.
        """
        
        print(f"DEBUG: Generating tests for {tool_name}...")
        try:
            response = completion(
                model=self.model,
                api_base=self.api_base,
                api_key=self.api_key,
                messages=[{"role": "user", "content": test_prompt}]
            )
            test_code = response.choices[0].message.content.strip()
             # Cleanup markdown if present
            if test_code.startswith("```python"):
                test_code = test_code.split("```python")[1]
            if test_code.endswith("```"):
                test_code = test_code.rsplit("```", 1)[0]
            test_code = test_code.strip()
            
        except Exception as e:
            return tool_code, None, f"LLM test generation failed: {e}"
            
        return tool_code, test_code, None

    def validate_tool(self, tool_name, tool_code, test_code):
        """
        Runs the tool and test in a Docker container.
        """
        # Create temp files
        # We should create these in the root or a temp dir to avoid cluttering deep dirs
        temp_tool_file = BASE_DIR / f"temp_{tool_name}.py"
        temp_test_file = BASE_DIR / f"temp_{tool_name}_test.py"
        tool_module_path = BASE_DIR / "tool_module.py"
        test_script_path = BASE_DIR / "test_script.py"
        
        try:
            with open(temp_tool_file, "w", encoding="utf-8") as f:
                f.write(tool_code)
         
            with open(tool_module_path, "w", encoding="utf-8") as f:
                f.write(tool_code)
            
            with open(test_script_path, "w", encoding="utf-8") as f:
                f.write(test_code)
            
            print("DEBUG: Running Docker validation...")
            
            # Mount BASE_DIR so docker sees the files in root
            cwd = str(BASE_DIR)
            
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{cwd}:/app",
                "-w", "/app",
                "python:3.9-slim",
                "python", "test_script.py"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if "TEST_PASSED" in result.stdout or result.returncode == 0:
                print("DEBUG: Validation Successful.")
                return True, result.stdout
            else:
                print(f"DEBUG: Validation Failed. Output:\n{result.stdout}\nError:\n{result.stderr}")
                return False, result.stdout + "\n" + result.stderr

        except Exception as e:
            return False, str(e)
        finally:
            # Cleanup temp files
            if os.path.exists(tool_module_path):
                os.remove(tool_module_path)
            if os.path.exists(test_script_path):
                os.remove(test_script_path)
            if os.path.exists(temp_tool_file):
                 os.remove(temp_tool_file)

    def save_tool(self, tool_name, tool_code, description):
        filename = f"{tool_name}.py"
        path = os.path.join(TOOLS_DIR, filename)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(tool_code)
            
        # Update definitions
        tool_def = {
            "name": tool_name,
            "description": description,
            "filename": filename,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Dynamic input"}
                }
            } 
        }
        
        try:
            with open(TOOL_DEFINITIONS_FILE, "r") as f:
                defs = json.load(f)
        except:
            defs = []
            
        defs.append(tool_def)
        
        with open(TOOL_DEFINITIONS_FILE, "w") as f:
            json.dump(defs, f, indent=4)
            
        return f"Tool '{tool_name}' saved to {path}"

    def create_tool(self, tool_name, description):
        """
        Orchestrates the creation flow.
        """
        print(f"Request: Create tool '{tool_name}' - {description}")
        
        tool_code, test_code, err = self.generate_tool_code(tool_name, description, "Implement efficient and clean code.")
        if err:
            return f"Failed to generate code: {err}"
            
        test_code = f"from tool_module import {tool_name}\n" + test_code.replace(f"from {tool_name} import", "# replaced import")
        
        success, log = self.validate_tool(tool_name, tool_code, test_code)
        
        if success:
            save_msg = self.save_tool(tool_name, tool_code, description)
            return {
                "status": "success",
                "message": save_msg,
                "tool_name": tool_name,
                "file_path": os.path.join(TOOLS_DIR, f"{tool_name}.py")
            }
        else:
            return {
                "status": "error",
                "message": f"Validation failed for tool '{tool_name}'. Logs: {log}"
            }

if __name__ == "__main__":
    creator = ToolCreator()
