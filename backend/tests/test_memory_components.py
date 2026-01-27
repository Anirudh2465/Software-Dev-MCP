from memory_manager import EpisodicMemory, SemanticMemory
import time

def test_memory():
    print("Testing Memory Systems...")
    
    # 1. Semantic Memory (MongoDB)
    print("\n--- Semantic Memory (MongoDB) ---")
    sem_mem = SemanticMemory()
    if sem_mem.collection is None:
        print("FAIL: Could not connect to MongoDB.")
    else:
        test_fact = f"Test Fact {int(time.time())}: Verify persistence."
        print(f"Saving fact: {test_fact}")
        result = sem_mem.save_fact(test_fact)
        print(result)
        
        print("Retrieving facts...")
        facts = sem_mem.get_all_facts()
        print("All Facts in DB:", facts)
        if test_fact in facts:
            print("SUCCESS: Fact found in DB.")
        else:
            print(f"FAIL: Fact not found. Found: {facts}")

    # 2. Episodic Memory (ChromaDB)
    print("\n--- Episodic Memory (ChromaDB) ---")
    epi_mem = EpisodicMemory()
    if epi_mem.collection is None:
        print("FAIL: Could not connect to ChromaDB.")
    else:
        test_content = f"Test Episode {int(time.time())}: User asked about verification."
        print(f"Adding episode: {test_content}")
        epi_mem.add_episode(test_content)
        
        print("Searching episode...")
        results = epi_mem.search_episodes("verification", n=1)
        if results and test_content in results:
             print("SUCCESS: Episode found.")
        else:
             print(f"FAIL: Episode not found or mismatch. Results: {results}")

if __name__ == "__main__":
    test_memory()
