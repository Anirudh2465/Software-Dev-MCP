from .celery_app import celery_app
from sentence_transformers import SentenceTransformer
import chromadb
import uuid
import datetime
import os

# Global model instance to avoid reloading per task if worker persists
# However, Celery forks, so we might need to load it lazily or at module level.
# At module level is standard for "warm" workers.
print("Loading Embedding Model...")
# Use a small efficient model
model = SentenceTransformer('all-MiniLM-L6-v2') 
print("Model Loaded.")

CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

@celery_app.task
def embed_and_store_episode(content: str, mode: str):
    """
    Background task to embed text and store in ChromaDB.
    """
    try:
        # Generate Embedding
        print(f"Embedding content for mode '{mode}'...")
        embedding = model.encode(content).tolist()
        
        # Connect to Chroma
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        
        # Consistent naming for partitioned collections
        collection_name = f"episodic_{mode.lower()}"
        collection = client.get_or_create_collection(name=collection_name)
        
        # Store
        metadata = {
            "content": content,
            "timestamp": datetime.datetime.now().isoformat(),
            "mode": mode
        }
        
        collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[content]
        )
        return f"Stored in {collection_name}"
    
    except Exception as e:
        print(f"Task Failed: {e}")
        return str(e)
