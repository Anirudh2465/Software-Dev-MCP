import chromadb
import json
import os
import sys
from pathlib import Path

# Connect to ChromaDB (assuming it's running via Docker on localhost:8000)
try:
    client = chromadb.HttpClient(host='localhost', port=8000)
    print("Connected to ChromaDB")
except Exception as e:
    print(f"Failed to connect to ChromaDB: {e}")
    sys.exit(1)

COLLECTION_NAME = "tools"

# Paths
# This script: jarvis/backend/scripts/tool_indexer.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent # jarvis/
DATA_DIR = BASE_DIR / "backend" / "data"
DUMMY_TOOLS_PATH = DATA_DIR / "dummy_tools.json"
TOOL_DEFINITIONS_PATH = BASE_DIR / "tool_definitions.json"

def index_tools():
    # Re-create collection to ensure clean state
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(name=COLLECTION_NAME)
    print(f"Created collection '{COLLECTION_NAME}'")

    # Load dummy tools
    tools = []
    if os.path.exists(DUMMY_TOOLS_PATH):
        with open(DUMMY_TOOLS_PATH, "r") as f:
            tools.extend(json.load(f))
    else:
        print(f"Warning: {DUMMY_TOOLS_PATH} not found.")

    # Load Dynamic Tools
    if os.path.exists(TOOL_DEFINITIONS_PATH):
        with open(TOOL_DEFINITIONS_PATH, "r") as f:
            try:
                dynamic_tools = json.load(f)
                tools.extend(dynamic_tools)
                print(f"Loaded {len(dynamic_tools)} dynamic tools.")
            except json.JSONDecodeError:
                print("Warning: tool_definitions.json is empty or invalid.")
    else:
        print(f"Warning: {TOOL_DEFINITIONS_PATH} not found.")

    if not tools:
        print("No tools found to index.")
        return

    ids = []
    documents = [] # We'll embed the description + name
    metadatas = []

    for tool in tools:
        tool_name = tool["name"]
        tool_desc = tool["description"]
        # Convert schema to string for metadata storage if needed, 
        # but for retrieval, we mostly need the full JSON to pass to LLM.
        # We can store the full JSON string in metadata or reconstruct it.
        # Storing in metadata is easiest for retrieval.
        
        ids.append(tool_name)
        # Embed the combination of name and description for semantic search validation
        documents.append(f"{tool_name}: {tool_desc}") 
        metadatas.append({"json": json.dumps(tool)})
        
    # Upsert
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    print(f"Successfully indexed {len(tools)} tools.")

if __name__ == "__main__":
    index_tools()
