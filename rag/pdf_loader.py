"""PDF text extraction, with a clear error for scanned / image-only PDFs."""

from pypdf import PdfReader


class ScannedPDFError(ValueError):
    """Raised when a PDF has no usable extractable text."""


def extract_pages(file_path):
    """Return a list of (page_number_1_based, text) tuples.

    Raises ScannedPDFError if the document yields almost no text, which
    is the usual sign of a scanned, image-only PDF. This is reported to
    the user as a clear error instead of producing an empty answer.
    """
    reader = PdfReader(file_path)
    pages = []
    total_chars = 0
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        pages.append((i, text))
        total_chars += len(text)
    if not pages:
        raise ScannedPDFError("This PDF has no pages.")
    # Heuristic: a real text PDF of even one page normally has far more
    # than this. Below it, the PDF is almost certainly image-only.
    if total_chars < 50:
        raise ScannedPDFError(
            "No extractable text was found in this PDF. It looks like a "
            "scanned, image-only PDF. Please upload a text-based PDF, or "
            "use OCR on the scanned file first and then upload the result."
        )
    return pages


def pages_to_text(pages):
    """Join pages into (page_number, text) items, skipping blank pages."""
    return [(page, text) for page, text in pages if text]
