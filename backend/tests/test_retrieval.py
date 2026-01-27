import chromadb
import json

CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

def test_retrieval(query):
    print(f"Query: '{query}'", flush=True)
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = client.get_collection("tools")
        print("Connected to ChromaDB.", flush=True)
        
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        
        print("Retrieved IDs:", results['ids'][0], flush=True)
        for meta in results['metadatas'][0]:
            tool = json.loads(meta['json'])
            print(f"- {tool['name']}: {tool['description']}", flush=True)
            
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    test_retrieval("Add a meeting with John to my calendar tomorrow at 2pm.")
    print("-" * 20)
    test_retrieval("List files in current directory.")
