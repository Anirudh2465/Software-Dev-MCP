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

@celery_app.task
def scan_directory(path: str):
    """
    Scans a directory and updates the snapshot in MongoDB.
    """
    import os
    from .services.file_monitor import FileMonitorService
    
    print(f"Scanning directory: {path}")
    service = FileMonitorService()
    
    if not os.path.exists(path):
        print(f"Directory not found: {path}")
        return "Directory not found"
        
    file_list = []
    try:
        # Walk the directory
        # Limit depth? User said "complete access", so full walk.
        # But be careful of massive node_modules.
        # We should probably respect .gitignore if possible, but for now raw scan.
        # We'll skip .git, __pycache__, node_modules for sanity.
        # We'll skip .git, __pycache__, node_modules for sanity.
        SKIP_DIRS = {'.git', '__pycache__', 'node_modules', 'venv', '.env', '.idea', '.vscode', 'dist', 'build', '.next'}
        
        for root, dirs, files in os.walk(path):
            # Modify dirs in-place to skip
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            
            for name in files:
                full_path = os.path.join(root, name)
                rel_path = os.path.relpath(full_path, path)
                
                file_list.append({
                   "rel_path": rel_path,
                   "type": "file",
                   "size": os.path.getsize(full_path)
                })
                
        service.update_snapshot(path, file_list)
        return f"Scanned {len(file_list)} files in {path}"
        
    except Exception as e:
        print(f"Scan failed: {e}")
        return f"Scan failed: {e}"

@celery_app.task
def scan_all_directories():
    """
    Periodic task to scan all monitored directories.
    """
    from .services.file_monitor import FileMonitorService
    service = FileMonitorService()
    dirs = service.get_directories()
    results = []
    for d in dirs:
        # Trigger scan for each
        # We can call synchronously or chain. Calling direct function since we are in a task.
        # But better to spawn sub-tasks? No, simple loop here is fine for now.
        res = scan_directory(d['path'])
        results.append(res)
    return results


