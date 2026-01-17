from memory_manager import SemanticMemory
from orchestrator import PromptManager
import time

def test_phase4():
    print("Testing Phase 4: Modes and Context...")
    
    # 1. Test Semantic Memory Categories
    print("\n--- Semantic Memory (Categories) ---")
    sem_mem = SemanticMemory()
    if sem_mem.collection is None:
        print("FAIL: No DB Connection")
        return

    ts = int(time.time())
    work_fact = f"Work Fact {ts}: Check email every morning."
    pers_fact = f"Personal Fact {ts}: I love hiking."
    
    print(sem_mem.save_fact(work_fact, category="work"))
    print(sem_mem.save_fact(pers_fact, category="personal"))
    
    all_facts = sem_mem.get_all_facts()
    work_facts = sem_mem.get_all_facts(category="work")
    pers_facts = sem_mem.get_all_facts(category="personal")
    
    print(f"All: {len(all_facts)}, Work: {len(work_facts)}, Personal: {len(pers_facts)}")
    
    if work_fact in work_facts and pers_fact not in work_facts:
        print("SUCCESS: Category filtering works.")
    else:
        print("FAIL: Filtering logic incorrect.")

    # 2. Test Prompt Manager
    print("\n--- Prompt Manager (Modes) ---")
    pm = PromptManager(sem_mem)
    
    # Default Mode (Work)
    print(f"Current Mode: {pm.mode}")
    prompt_work = pm.get_system_prompt()
    if "[CURRENT_MODE]\nCurrent Mode: Work" in prompt_work:
        print("SUCCESS: Default mode is Work.")
    
    if work_fact in prompt_work:
         print("SUCCESS: Work fact present in Work mode.")
    else:
         print("WARNING: Work fact missing in Work mode (Logic might be specific).")

    # Switch to Personal
    pm.set_mode("Personal")
    print(f"Switched to: {pm.mode}")
    prompt_pers = pm.get_system_prompt()
    
    if "[CURRENT_MODE]\nCurrent Mode: Personal" in prompt_pers:
        print("SUCCESS: Mode switched to Personal.")
        
    if pers_fact in prompt_pers:
        print("SUCCESS: Personal fact present in Personal mode.")
    
    # Check simple exclusion logic (if implemented)
    # My logic: Personal Mode gets Personal + General. Work Mode gets Work + General.
    if work_fact not in prompt_pers:
        print("SUCCESS: Work fact EXCLUDED from Personal mode.")
    else:
        print("FAIL: Work fact leaked into Personal mode.")

if __name__ == "__main__":
    test_phase4()
