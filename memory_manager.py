import chromadb
from pymongo import MongoClient
import datetime
import uuid
import os

class EpisodicMemory:
    def __init__(self, host="localhost", port=8000):
        try:
            self.client = chromadb.HttpClient(host=host, port=port)
            self.collection = self.client.get_or_create_collection(name="episodic_memory")
            print(f"Connected to ChromaDB episodic_memory at {host}:{port}")
        except Exception as e:
            print(f"Error connecting to ChromaDB: {e}")
            self.collection = None

    def add_episode(self, content, metadata=None):
        if self.collection is None:
            return
        
        if metadata is None:
            metadata = {}
        
        metadata["timestamp"] = datetime.datetime.now().isoformat()
        
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())]
        )

    def search_episodes(self, query, n=3):
        if self.collection is None:
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n
            )
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            print(f"Error searching episodes: {e}")
            return []

class SemanticMemory:
    def __init__(self, uri="mongodb://localhost:27017/"):
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            self.db = self.client["jarvis_db"]
            self.collection = self.db["facts"]
            # Check connection
            self.client.server_info()
            print(f"Connected to MongoDB at {uri}")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            self.collection = None

    def save_fact(self, fact, category="general"):
        if self.collection is None:
            return "Error: MongoDB not available."
            
        doc = {
            "fact": fact,
            "category": category,
            "timestamp": datetime.datetime.now().isoformat()
        }
        try:
            self.collection.insert_one(doc)
            return f"Fact saved ({category}): {fact}"
        except Exception as e:
            return f"Error saving fact: {e}"

    def get_all_facts(self, category=None):
        if self.collection is None:
            return []
            
        try:
            query = {}
            if category:
                query["category"] = category
                
            cursor = self.collection.find(query, {"_id": 0, "fact": 1})
            return [doc["fact"] for doc in cursor]
        except Exception as e:
            print(f"Error retrieving facts: {e}")
            return []
