import fitz  # PyMuPDF — imported as 'fitz'
import base64


def pdf_to_images(pdf_path: str) -> list:
    """
    Converts every page of a PDF into a base64-encoded PNG image.
    Works for both digital PDFs and scanned/photographed documents.
    Returns a list of base64 strings, one per page.
    """
    doc = fitz.open(pdf_path)
    images = []

    for page_number in range(len(doc)):
        page = doc[page_number]
        # dpi=150 is a good balance of quality vs speed
        pix = page.get_pixmap(dpi=150)
        # Convert page to PNG bytes
        img_bytes = pix.tobytes("png")
        # Encode to base64 so it can be sent to Claude API
        img_base64 = base64.standard_b64encode(img_bytes).decode("utf-8")
        images.append(img_base64)

    doc.close()
    return images


def get_page_count(pdf_path: str) -> int:
    """Returns the number of pages in a PDF. Useful for progress display."""
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count
