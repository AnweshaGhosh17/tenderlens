import fitz  # PyMuPDF — imported as 'fitz'


def get_page_count(pdf_path: str) -> int:
    """Returns the number of pages in a PDF. Useful for progress display."""
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count


def pdf_to_text(pdf_path: str) -> str:
    """
    Extracts raw text from a digital (non-scanned) PDF.
    Useful for quick text checks before sending to Gemini.
    """
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text
