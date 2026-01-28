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
def embed_and_store_episode(content: str, mode: str, user_id: str):
    """
    Background task to embed text and store in ChromaDB.
    """
    try:
        # Generate Embedding
        print(f"Embedding content for mode '{mode}' user '{user_id}'...")
        embedding = model.encode(content).tolist()
        
        # Connect to Chroma
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        
        # User-specific collection
        collection_name = f"episodic_{user_id}_{mode.lower()}"
        collection = client.get_or_create_collection(name=collection_name)
        
        # Store
        metadata = {
            "content": content,
            "timestamp": datetime.datetime.now().isoformat(),
            "mode": mode,
            "user_id": user_id
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

@celery_app.task
def initialize_user_partition(username: str):
    """
    Initialize default memory partitions for a new user.
    """
    try:
        print(f"Initializing partitions for user: {username}")
        # We can pre-create collections or just log it. 
        # Chroma creates on demand, so maybe just add a welcome fact to Semantic Memory?
        
        # For now, let's just log and maybe create a default 'welcome' episode (optional)
        # But since we need SemanticMemory access, we might need to instantiate it or just modify this task later.
        
        # Simulating initialization
        return f"User partition initialized for {username}"
    except Exception as e:
        return f"Initialization failed: {e}"
