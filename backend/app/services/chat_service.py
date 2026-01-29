import os
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

class ChatService:
    def __init__(self):
        self.client = None
        self.collection = None
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client["jarvis_db"]
            self.collection = self.db["chats"]
            print("ChatService: Connected to MongoDB")
        except Exception as e:
            print(f"ChatService: Error connecting to MongoDB: {e}")

    def create_chat(self, user_id, mode, title="New Chat"):
        if self.collection is None:
            return None
        
        doc = {
            "user_id": user_id,
            "mode": mode,
            "title": title,
            "created_at": datetime.utcnow().isoformat(),
            "messages": []
        }
        result = self.collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    def get_chats(self, user_id, mode):
        if self.collection is None:
            return []
        
        cursor = self.collection.find({"user_id": user_id, "mode": mode}).sort("created_at", -1)
        chats = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            chats.append(doc)
        return chats

    def get_chat(self, chat_id, user_id):
        if self.collection is None:
            return None
        try:
            doc = self.collection.find_one({"_id": ObjectId(chat_id), "user_id": user_id})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except:
            return None

    def add_message(self, chat_id, user_id, role, content):
        if self.collection is None:
            return False
        
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(chat_id), "user_id": user_id},
                {"$push": {"messages": msg}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding message to chat {chat_id}: {e}")
            return False

    def delete_chat(self, chat_id, user_id):
        if self.collection is None:
            return False
        try:
            result = self.collection.delete_one({"_id": ObjectId(chat_id), "user_id": user_id})
            return result.deleted_count > 0
        except:
            return False
