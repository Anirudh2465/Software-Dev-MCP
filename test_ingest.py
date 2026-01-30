from pypdf import PdfWriter
from backend.app.services.document_manager import DocumentManager
import os

# Create dummy PDF
pdf_path = "test_document.pdf"
writer = PdfWriter()
writer.add_blank_page(width=72, height=72)
with open(pdf_path, "wb") as f:
    writer.write(f)

print(f"Created {pdf_path}")

# Test Ingestion
dm = DocumentManager()
print(f"Testing ingestion of {pdf_path}...")
result = dm.ingest_file(os.path.abspath(pdf_path))
print(f"Result: {result}")

# Cleanup
if os.path.exists(pdf_path):
    os.remove(pdf_path)
