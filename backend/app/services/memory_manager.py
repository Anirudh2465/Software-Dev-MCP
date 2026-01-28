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

    def add_episode(self, content, mode="Work", user_id="default"):
        # Offload to Celery
        print(f"Dispatching memory task for mode '{mode}' user '{user_id}'")
        embed_and_store_episode.delay(content, mode, user_id)

    def search_episodes(self, query, mode="Work", n=3, user_id="default"):
        if not self.client or not self.model:
            return []
            
        try:
            # Generate query embedding locally independent of Celery
            query_embedding = self.model.encode(query).tolist()
            
            collection_name = f"episodic_{user_id}_{mode.lower()}"
            collection = self.client.get_or_create_collection(name=collection_name)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n
            )
            
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            print(f"Error searching episodes: {e}")
            return []
            
    def delete_mode_memory(self, mode, user_id="default"):
        if not self.client:
            return False
        try:
            collection_name = f"episodic_{user_id}_{mode.lower()}"
            self.client.delete_collection(name=collection_name)
            return True
        except Exception as e:
            print(f"Error deleting mode {mode}: {e}")
            return False

    def get_all_episodes(self, mode="Work", user_id="default"):
        if not self.client:
             return []
        try:
            collection_name = f"episodic_{user_id}_{mode.lower()}"
            collection = self.client.get_or_create_collection(name=collection_name)
            # get all
            results = collection.get()
            # Construct list of dicts
            episodes = []
            if results['ids']:
                for i, id_val in enumerate(results['ids']):
                     episodes.append({
                         "id": id_val,
                         "content": results['documents'][i],
                         "metadata": results['metadatas'][i] if results['metadatas'] else {}
                     })
            return episodes
        except Exception as e:
            print(f"Error getting all episodes: {e}")
            return []

    def delete_episode(self, episode_id, mode="Work", user_id="default"):
        if not self.client:
             return False
        try:
            collection_name = f"episodic_{user_id}_{mode.lower()}"
            collection = self.client.get_collection(name=collection_name)
            collection.delete(ids=[episode_id])
            return True
        except Exception as e:
             print(f"Error deleting episode {episode_id}: {e}")
             return False

    def delete_episodes_containing(self, text, mode="Work", user_id="default"):
        """
        Hard delete episodes containing traces of deleted memories using Semantic Search.
        This finds episodes semantically similar to the deleted fact (e.g. "Saved: [fact]") and deletes them.
        """
        if not self.client or not self.model:
             return 0
             
        try:
            # 1. Generate embedding for the fact
            query_embedding = self.model.encode(text).tolist()
            
            collection_name = f"episodic_{user_id}_{mode.lower()}"
            collection = self.client.get_or_create_collection(name=collection_name)
            
            # 2. Search for TOP N results (e.g., top 5) that match this fact
            # likely candidates are "User: save X", "Jarvis: Saved X", etc.
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5 
            )
            
            ids_to_delete = []
            if results and results['ids'] and results['ids'][0]:
                 # 3. Filter results: 
                 # We can just delete the top matches blindly, or check distance.
                 # Chroma default distance is L2. Lower is better.
                 # Let's be aggressive for now on the top 3-5, or maybe just delete them all.
                 # Given the user wants to "bypass" history, let's delete the top matches.
                 # To be safer, we could log them.
                 
                 found_ids = results['ids'][0]
                 found_docs = results['documents'][0]
                 
                 print(f"Semantic Deletion Candidates for '{text}': {found_docs}")
                 ids_to_delete = found_ids

            if not ids_to_delete:
                return 0

            collection.delete(ids=ids_to_delete)
            print(f"Hard deleted {len(ids_to_delete)} episodes semantically related to '{text}'")
            return len(ids_to_delete)
            
        except Exception as e:
             print(f"Error deleting episodes containing text: {e}")
             return 0


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

    def save_fact(self, fact, mode="Work", user_id="default"):
        if self.collection is None:
            return "Error: Database not connected."
            
        doc = {
            "fact": fact,
            "mode": mode, # Partition by mode
            "user_id": user_id,
            "timestamp": datetime.datetime.now().isoformat()
        }
        try:
            self.collection.insert_one(doc)
            return f"Fact saved to {mode}: {fact}"
        except Exception as e:
            return f"Error saving fact: {e}"

    def get_all_facts(self, mode="Work", user_id="default"):
        if self.collection is None:
            return []
            
        try:
            # Simple partition: Just get facts for this mode
            cursor = self.collection.find({"mode": mode, "user_id": user_id})
            facts = []
            for doc in cursor:
                facts.append({
                    "id": str(doc["_id"]),
                    "fact": doc["fact"],
                    "timestamp": doc.get("timestamp", "")
                })
            return facts
        except Exception as e:
            print(f"Error retrieving facts: {e}")
            return []
            
    def get_modes(self):
        if self.collection is None:
            return ["Work", "Personal"] # Default
        try:
            modes = self.collection.distinct("mode")
            default_modes = ["Work", "Personal"]
            all_modes = list(set(modes + default_modes))
            return all_modes
        except Exception as e:
            print(f"Error fetching modes: {e}")
            return ["Work", "Personal"]

    def delete_mode(self, mode, user_id="default"):
        if self.collection is None:
            return False
        try:
            self.collection.delete_many({"mode": mode, "user_id": user_id})
            return True
        except Exception as e:
             print(f"Error deleting mode {mode} from Mongo: {e}")
             return False

    def delete_fact(self, fact_id):
        if self.collection is None:
             return None
        try:
            from bson.objectid import ObjectId
            doc = self.collection.find_one({"_id": ObjectId(fact_id)})
            if doc:
                self.collection.delete_one({"_id": ObjectId(fact_id)})
                return doc # Return the whole document (specifically 'fact' and 'mode' are useful)
            return None
        except Exception as e:
             print(f"Error deleting fact {fact_id}: {e}")
             return None

    # Helper for EpisodicMemory is not in this class, checking indentation...
    # Wait, I need to add delete_episodes_containing to EpisodicMemory class above.

