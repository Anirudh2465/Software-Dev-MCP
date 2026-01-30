try:
    import pypdf
    print("pypdf available")
except ImportError as e:
    print(f"pypdf FAILED: {e}")

try:
    import docx
    print("python-docx available")
except ImportError as e:
    print(f"python-docx FAILED: {e}")

try:
    from PIL import Image
    print("Pillow available")
except ImportError as e:
    print(f"Pillow FAILED: {e}")

try:
    import pytesseract
    print("pytesseract available")
except ImportError as e:
    print(f"pytesseract FAILED: {e}")
