import os
import json
import subprocess
import time
from litellm import completion

TOOLS_DIR = "tools"
TOOL_DEFINITIONS_FILE = "tool_definitions.json"

class ToolCreator:
    def __init__(self, model="openai/local-model", api_base="http://127.0.0.1:1234/v1", api_key="lm-studio"):
        self.model = model
        self.api_base = api_base
        self.api_key = api_key
        
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
        temp_tool_file = f"temp_{tool_name}.py"
        temp_test_file = f"temp_{tool_name}_test.py"
        
        try:
            with open(temp_tool_file, "w", encoding="utf-8") as f:
                f.write(tool_code)
                
            # The test needs to import the tool. 
            # We'll prepend the tool code to the test code for simplicity in the sandbox, 
            # OR we can just rely on file presence if we mount the dir.
            # Simpler approach for one-off script: Concatenate.
            
            # Actually, let's try to mock the import by just pasting the function at the top of the test file
            # But the test code expects "from tool_module import ..."
            # Let's adjust the test code or just write a unified validator.
            
            unified_test_code = f"""
import sys
import os

# --- Tool Code Injected Below ---
{tool_code}
# ------------------------------

if __name__ == "__main__":
    try:
        # We need to adapt the generated test code which might try to import.
        # Let's just wrap the generated test logic.
        # But since the LLM wrote imports, we might have issues.
        # Hack: Ask LLM to write a self-contained test, or just strip the import line.
        pass
""" 
            # Re-thinking: Safest is to mount the directory and run python.
            # But we are in a windows environment calling docker.
            # Let's use `docker run -v %cd%:/app ...`
            
            # We will create the files locally:
            # tool_module.py (fixed name so the test can import it easily)
            # test_script.py
            
            with open("tool_module.py", "w", encoding="utf-8") as f:
                f.write(tool_code)
            
            with open("test_script.py", "w", encoding="utf-8") as f:
                f.write(test_code)
            
            print("DEBUG: Running Docker validation...")
            # Use docker to run the test
            # Assumes python:3.9-slim is available.
            # We mount current directory to /app
            cwd = os.getcwd()
            
            # Windows path handling for Docker mount might be tricky.
            # Let's try to just run a container and pass code via stdin or echo if simple.
            # But mounting is reliable. 
            
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
            if os.path.exists("tool_module.py"):
                os.remove("tool_module.py")
            if os.path.exists("test_script.py"):
                os.remove("test_script.py")
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
            # Note: We are cheating a bit on schema. In a real system, we'd ask LLM to generate the JSON schema too.
            # For this prototype, we will assume tools take generic args or we ask LLM for the schema as well.
        }
        
        # Let's simple-fix the schema issue: Ask LLM for the schema during code gen or inferred.
        # Making it simple: All tools created this way will be documented as "See description".
        
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
            
        # Refine Test Code to import correctly
        # The test code generated by LLM might imagine a module name.
        # We enforce "from tool_module import tool_name" strictly in our temp file setup.
        # We need to ensure the test code actually does that.
        test_code = f"from tool_module import {tool_name}\n" + test_code.replace(f"from {tool_name} import", "# replaced import")
        
        success, log = self.validate_tool(tool_name, tool_code, test_code)
        
        if success:
            return self.save_tool(tool_name, tool_code, description)
        else:
            return f"Validation failed for tool '{tool_name}'. Logs: {log}"

if __name__ == "__main__":
    # Test stub
    creator = ToolCreator()
    # print(creator.create_tool("reverse_string", "Reverse the provided string text."))
