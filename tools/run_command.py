import subprocess
import os

def run_command(command: str, cwd: str = ".") -> str:
    """
    Execute a shell command.
    """
    try:
        # Resolve absolute path for cwd if it's relative
        if not os.path.isabs(cwd):
            cwd = os.path.abspath(cwd)
            
        if not os.path.exists(cwd):
            return f"Error: Working directory '{cwd}' does not exist."

        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120 # 2 minute timeout
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
            
        return output if output.strip() else "Command executed successfully with no output."
        
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error executing command: {str(e)}"
