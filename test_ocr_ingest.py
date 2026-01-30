from backend.app.services.document_manager import DocumentManager
from PIL import Image, ImageDraw, ImageFont
import os
import io
from pypdf import PdfWriter, PdfReader

# 1. Create an image with text
img = Image.new('RGB', (500, 200), color = (255, 255, 255))
d = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("arial.ttf", 24)
except:
    font = ImageFont.load_default()
    
d.text((10,10), "This is a test of OCR functionality inside a PDF.", fill=(0,0,0), font=font)

# Save image to bytes
img_bytes = io.BytesIO()
img.save(img_bytes, format='PDF')
img_bytes.seek(0)

# 2. Save as PDF file
pdf_path = "test_ocr.pdf"
with open(pdf_path, "wb") as f:
    f.write(img_bytes.read())

print(f"Created image-based PDF: {pdf_path}")

# 3. Test Ingestion
dm = DocumentManager()
print(f"Testing OCR ingestion of {pdf_path}...")
result = dm.ingest_file(os.path.abspath(pdf_path))
print(f"Result: {result}")

# 4. cleanup
if os.path.exists(pdf_path):
    os.remove(pdf_path)
