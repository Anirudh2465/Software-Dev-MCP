from fastmcp import FastMCP
import os
import importlib.util
import sys
from pathlib import Path

# Create an MCP server
mcp = FastMCP("Local Filesystem Server")

# Define Paths
# File is in jarvis/backend/scripts/filesystem_server.py
# Root is jarvis/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = BASE_DIR / "tools"

@mcp.tool()
def list_directory(path: str) -> str:
    """List the contents of a directory."""
    try:
        if not os.path.isdir(path):
            return f"Error: Path '{path}' is not a directory."
        files = os.listdir(path)
        return "\n".join(files) if files else "Directory is empty."
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def read_file(path: str) -> str:
    """Read specific file contents."""
    try:
        if not os.path.isfile(path):
            return f"Error: File '{path}' not found."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Create or overwrite a file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to '{path}'."
    except Exception as e:
        return f"Error: {str(e)}"

def load_dynamic_tools():
    if not os.path.exists(TOOLS_DIR):
        return

    for filename in os.listdir(TOOLS_DIR):
        if filename.endswith(".py") and not filename.startswith("temp_"):
            tool_name = filename[:-3]
            file_path = os.path.join(TOOLS_DIR, filename)
            
            try:
                spec = importlib.util.spec_from_file_location(tool_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for the function matching the tool name
                    if hasattr(module, tool_name):
                        func = getattr(module, tool_name)
                        # Register with FastMCP
                        mcp.tool()(func)
                        print(f"Loaded dynamic tool: {tool_name}")
            except Exception as e:
                print(f"Failed to load tool {tool_name}: {e}")

load_dynamic_tools()

if __name__ == "__main__":
    mcp.run()
