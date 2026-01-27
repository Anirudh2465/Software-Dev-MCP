import os
import datetime
import uuid
import json
from pymongo import MongoClient
import chromadb
from sentence_transformers import SentenceTransformer
from ..tasks import embed_and_store_episode

# Env vars should be loaded by orchestrator or main before importing, 
# or we load them here.
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

class EpisodicMemory:
    def __init__(self):
        self.model = None
        self.client = None
        try:
            # We only need the model for SEARCH (Reading)
            # Writing is handled by Celery
            print("Loading Search Embedding Model (Local)...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        except Exception as e:
            print(f"Error initializing EpisodicMemory: {e}")

    def add_episode(self, content, mode="Work"):
        # Offload to Celery
        print(f"Dispatching memory task for mode '{mode}'")
        embed_and_store_episode.delay(content, mode)

    def search_episodes(self, query, mode="Work", n=3):
        if not self.client or not self.model:
            return []
            
        try:
            # Generate query embedding locally independent of Celery
            query_embedding = self.model.encode(query).tolist()
            
            collection_name = f"episodic_{mode.lower()}"
            collection = self.client.get_or_create_collection(name=collection_name)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n
            )
            
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            print(f"Error searching episodes: {e}")
            return []
            
    def delete_mode_memory(self, mode):
        if not self.client:
            return False
        try:
            collection_name = f"episodic_{mode.lower()}"
            self.client.delete_collection(name=collection_name)
            return True
        except Exception as e:
            print(f"Error deleting mode {mode}: {e}")
            return False

class SemanticMemory:
    def __init__(self):
        self.client = None
        self.collection = None
        
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client["jarvis_db"]
            self.collection = self.db["facts"]
            print("Connected to MongoDB Local")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")

    def save_fact(self, fact, mode="Work"):
        if self.collection is None:
            return "Error: Database not connected."
            
        doc = {
            "fact": fact,
            "mode": mode, # Partition by mode
            "timestamp": datetime.datetime.now().isoformat()
        }
        try:
            self.collection.insert_one(doc)
            return f"Fact saved to {mode}: {fact}"
        except Exception as e:
            return f"Error saving fact: {e}"

    def get_all_facts(self, mode="Work"):
        if self.collection is None:
            return []
            
        try:
            # Simple partition: Just get facts for this mode
            cursor = self.collection.find({"mode": mode}, {"_id": 0, "fact": 1})
            return [doc["fact"] for doc in cursor]
        except Exception as e:
            print(f"Error retrieving facts: {e}")
            return []
            
    def get_modes(self):
        if self.collection is None:
            return ["Work", "Personal"] # Default
        try:
            modes = self.collection.distinct("mode")
            return list(set(modes + ["Work", "Personal"])) # Ensure defaults exist
        except Exception as e:
            print(f"Error fetching modes: {e}")
            return ["Work", "Personal"]

    def delete_mode(self, mode):
        if self.collection is None:
            return False
        try:
            self.collection.delete_many({"mode": mode})
            return True
        except Exception as e:
             print(f"Error deleting mode {mode} from Mongo: {e}")
             return False
