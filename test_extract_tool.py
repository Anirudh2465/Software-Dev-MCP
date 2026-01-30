from tools.extract_pdf_text import extract_pdf_text
import os

# Create dummy PDF for testing
from pypdf import PdfWriter
pdf_path = "test_extract.pdf"
writer = PdfWriter()
page = writer.add_blank_page(width=72, height=72)
# Adding text is complex with pypdf writers directly, usually we merge.
# Let's just create a blank one and expect it not to crash (it returns empty string or specific message)
with open(pdf_path, "wb") as f:
    writer.write(f)

print(f"Testing extract_pdf_text on {pdf_path}...")
result = extract_pdf_text(os.path.abspath(pdf_path))
print(f"Result: '{result}'")

if os.path.exists(pdf_path):
    os.remove(pdf_path)
