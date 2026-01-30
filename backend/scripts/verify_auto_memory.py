import asyncio
import sys
from pathlib import Path

# Fix path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.app.services.orchestrator import JarvisOrchestrator

# Mocking acompletion again to simulate extraction
async def mock_acompletion(*args, **kwargs):
    class MockResponse:
        class Choices:
            class Message:
                # Simulate extraction response
                content = '```json\n{"facts": ["User likes automated verification"]}\n```'
            message = Message()
            choices = [Choices()]
        choices = [Choices()]
    return MockResponse()

import backend.app.services.orchestrator
backend.app.services.orchestrator.acompletion = mock_acompletion

async def test_auto_extraction():
    print("Testing Auto-Extraction...")
    orchestrator = JarvisOrchestrator()
    
    # We want to call _extract_and_save_facts directly to verify logic, 
    # as process_message creates a background task which might be hard to capture in a short script without sleep.
    
    print("Calling _extract_and_save_facts...")
    await orchestrator._extract_and_save_facts(
        user_input="I love automated verification tools.",
        assistant_output="That is great to hear!",
        user_id="test_user"
    )
    
    print("Checking Semantic Memory...")
    # Verify it called save_fact (we can check the print output or mock semantic memory)
    # Since we can't easily mock semantic memory instance inside orchestrator without patching __init__,
    # we relies on the side effect or logs.
    # But wait, we can inspect orchestrator.semantic_memory.collection via the real DB if it connects?
    # Or we can just check if it ran without error and verify manually via recent facts?
    
    facts = orchestrator.semantic_memory.get_all_facts(mode="Work", user_id="test_user")
    found = any("User likes automated verification" in f['fact'] for f in facts)
    
    if found:
        print("SUCCESS: Fact was extracted and saved.")
    else:
        print("FAILURE: Fact not found in DB.")

if __name__ == "__main__":
    asyncio.run(test_auto_extraction())
