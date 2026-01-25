import chromadb
import json
import os
import sys

# Connect to ChromaDB (assuming it's running via Docker on localhost:8000)
try:
    client = chromadb.HttpClient(host='localhost', port=8000)
    print("Connected to ChromaDB")
except Exception as e:
    print(f"Failed to connect to ChromaDB: {e}")
    sys.exit(1)

COLLECTION_NAME = "tools"

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
    if os.path.exists("dummy_tools.json"):
        with open("dummy_tools.json", "r") as f:
            tools.extend(json.load(f))

    # Load Dynamic Tools
    if os.path.exists("tool_definitions.json"):
        with open("tool_definitions.json", "r") as f:
            try:
                dynamic_tools = json.load(f)
                tools.extend(dynamic_tools)
                print(f"Loaded {len(dynamic_tools)} dynamic tools.")
            except json.JSONDecodeError:
                print("Warning: tool_definitions.json is empty or invalid.")

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
