# REQUIREMENTS: pypdf
from typing import Dict, Union

def extract_text_from_pdf(pdf_path: str) -> Union[str, Dict]:
    """
    Extracts all text from a PDF file.

    Parameters:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: The concatenated text extracted from the PDF.
    """
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError("pypdf is required but not installed.") from e

    if not isinstance(pdf_path, str):
        raise TypeError("pdf_path must be a string path to the PDF file")

    reader = PdfReader(pdf_path)
    text_chunks = []

    for page_num in range(len(reader.pages)):
        try:
            page = reader.pages[page_num]
            text = page.extract_text()
            if text:
                text_chunks.append(text.strip())
        except Exception:
            # Skip pages that cannot be processed
            continue

    full_text = "\n".join(text_chunks)
    return full_text if full_text else ""