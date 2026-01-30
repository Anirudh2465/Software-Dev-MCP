import pytesseract
import shutil

# Check if tesseract is in PATH
tesseract_cmd = shutil.which("tesseract")
print(f"Tesseract Path: {tesseract_cmd}")

try:
    print(f"Tesseract Version: {pytesseract.get_tesseract_version()}")
except Exception as e:
    print(f"Tesseract Execution Failed: {e}")
