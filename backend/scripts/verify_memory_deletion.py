
import os
import sys
import asyncio
from pymongo import MongoClient
import uuid

# Adjust path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Mock sentence_transformers to avoid dependency issues for SemanticMemory test
from unittest.mock import MagicMock
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["chromadb"] = MagicMock() # Also mock chromadb if not needed

from app.services.memory_manager import SemanticMemory

def test_memory_lifecycle():
    print("Initializing SemanticMemory...")
    memory = SemanticMemory()
    
    user_id = "test_user_" + str(uuid.uuid4())[:8]
    mode = "Work"
    fact_content = f"Test Fact {uuid.uuid4()}"
    
    print(f"User: {user_id}, Mode: {mode}")
    
    # 1. Save Fact
    print(f"Saving fact: '{fact_content}'")
    result = memory.save_fact(fact_content, mode=mode, user_id=user_id)
    print(f"Save Result: {result}")
    
    # 2. Verify it exists
    facts = memory.get_all_facts(mode=mode, user_id=user_id)
    print(f"Facts after save: {[f['fact'] for f in facts]}")
    
    saved_fact = next((f for f in facts if f['fact'] == fact_content), None)
    if not saved_fact:
        print("ERROR: Fact not found after save!")
        return
    
    fact_id = saved_fact['id']
    print(f"Fact ID: {fact_id}")
    
    # 3. Delete Fact
    print(f"Deleting fact ID: {fact_id}")
    delete_result = memory.delete_fact(fact_id)
    print(f"Delete Result: {delete_result}")
    
    # 4. Verify it's gone
    facts_after = memory.get_all_facts(mode=mode, user_id=user_id)
    print(f"Facts after delete: {[f['fact'] for f in facts_after]}")
    
    deleted_fact = next((f for f in facts_after if f['fact'] == fact_content), None)
    if deleted_fact:
        print("ERROR: Fact STILL EXISTS after delete!")
    else:
        print("SUCCESS: Fact is gone.")

if __name__ == "__main__":
    test_memory_lifecycle()
