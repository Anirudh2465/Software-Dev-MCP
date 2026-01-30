# REQUIREMENTS: pypdf

import pypdf

def extract_pdf_text(file_path):
    """
    Extracts and returns the full textual content of a PDF file as a single string.
    
    Parameters
    ----------
    file_path : str
        Path to the PDF file on disk.

    Returns
    -------
    str
        Concatenated text from all pages of the PDF. If extraction fails, an error message is returned.
    """
    try:
        # Open in binary mode just to be safe, though pypdf handles paths too
        reader = pypdf.PdfReader(file_path)
        text_chunks = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
        
        full_text = "\n".join(text_chunks)
        if not full_text:
            return "[PDF extracted but no text found. It might be an image-based PDF which requires OCR.]"
        return full_text
        
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"