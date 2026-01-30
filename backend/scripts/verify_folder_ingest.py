import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.app.services.document_manager import DocumentManager
import os

def test_recursive_ingest():
    print("Testing Recursive Ingestion...")
    dm = DocumentManager()
    
    # Create test dir structure
    test_dir = Path("test_ingest_data")
    test_dir.mkdir(exist_ok=True)
    (test_dir / "root.txt").write_text("Root content")
    
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir(exist_ok=True)
    (sub_dir / "sub.txt").write_text("Subdir content")
    
    # Run ingestion
    print(f"Ingesting {test_dir.resolve()}...")
    result = dm.ingest_directory(str(test_dir.resolve()))
    print(result)
    
    # Verify results
    if "root.txt" in result and "sub.txt" in result:
        print("SUCCESS: Both files found in result output.")
    else:
        print("FAILURE: Files logic check failed.")
        
    # Start cleanup
    import shutil
    shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_recursive_ingest()
