import fitz  # PyMuPDF


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a digital (non-scanned) PDF.
    Returns the concatenated text of all pages.
    """
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def is_digital_pdf(file_path: str, min_chars: int = 20) -> bool:
    """
    Rough check: if PyMuPDF can extract a reasonable amount of text,
    treat it as a digital PDF. If it extracts almost nothing, it's
    likely scanned and needs OCR instead.
    """
    text = extract_text_from_pdf(file_path)
    return len(text.strip()) >= min_chars