# REQUIREMENTS: PyPDF2

import PyPDF2

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
        Concatenated text from all pages of the PDF. If extraction fails, an empty string is returned.
    """
    try:
        with open(file_path, "rb") as fp:
            reader = PyPDF2.PdfReader(fp)
            text_chunks = []
            for page in reader.pages:
                # Some PDFs may contain no text on a page; skip if None
                page_text = page.extract_text()
                if page_text:
                    text_chunks.append(page_text)
        return "\n".join(text_chunks)
    except Exception:
        # Return empty string to indicate failure without raising an exception
        return ""