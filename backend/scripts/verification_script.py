import pymongo
import chromadb
import os

def check_mongo():
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        print("SUCCESS: Connected to MongoDB")
    except Exception as e:
        print(f"FAILURE: Could not connect to MongoDB: {e}")

def check_chroma():
    try:
        client = chromadb.HttpClient(host='localhost', port=8000)
        client.heartbeat()
        print("SUCCESS: Connected to ChromaDB")
    except Exception as e:
        print(f"FAILURE: Could not connect to ChromaDB: {e}")

if __name__ == "__main__":
    print("Starting verification...")
    check_mongo()
    check_chroma()
