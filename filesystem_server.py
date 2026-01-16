from fastmcp import FastMCP
import os

# Create an MCP server
mcp = FastMCP("Local Filesystem Server")

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

if __name__ == "__main__":
    mcp.run()
