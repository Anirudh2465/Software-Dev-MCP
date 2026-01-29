import subprocess
import sys
import json
import os

def run():
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    print("Launching server...", flush=True)
    proc = subprocess.Popen(
        [sys.executable, "filesystem_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    # Send initialize
    # FastMCP uses interacting with the MCP protocol. 
    # Example init message.
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05", # Use a recent version
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    
    print("Sending init...", flush=True)
    try:
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        
        print("Reading response...", flush=True)
        response = proc.stdout.readline()
        print(f"Response: {response}", flush=True)
    except Exception as e:
        print(f"Error communicating: {e}")
    
    # Read stderr non-blocking or just close and read
    proc.terminate()
    try:
        outs, errs = proc.communicate(timeout=2)
        print(f"Stdout remainder: {outs}")
        print(f"Stderr: {errs}")
    except:
        pass

if __name__ == "__main__":
    run()
