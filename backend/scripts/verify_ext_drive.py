from pathlib import Path
import os
import sys

# Attempt to verify if we can read from D drive
def test_external_drive():
    target_path = Path("D:/New Folder/random_data.csv")
    print(f"Checking if {target_path} exists...")
    
    if target_path.exists():
        print("File exists!")
        try:
            content = target_path.read_text()
            print(f"Content read successfully. Length: {len(content)}")
            print("Snippet:", content[:100])
        except Exception as e:
            print(f"Error reading file: {e}")
    else:
        print("File does not exist. Attempting to create a mock file on D drive (if possible)...")
        # Ensure D drive exists
        if Path("D:/").exists():
            try:
                test_file = Path("D:/test_mcp_access.txt")
                test_file.write_text("Hello from MCP agent")
                print(f"Successfully wrote to {test_file}")
                print("Read back:", test_file.read_text())
                test_file.unlink()
                print("Cleanup successful.")
            except Exception as e:
                print(f"Cannot write to D drive: {e}")
        else:
            print("D drive not found.")

if __name__ == "__main__":
    test_external_drive()
