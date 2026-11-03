"""Overlapping chunking.

Choice: ~500 characters per chunk with ~100 characters of overlap.

Why: a chunk much larger than this dilutes retrieval (one chunk covers
several unrelated ideas, so a query matches weakly), while a chunk much
smaller loses context (a sentence alone may not say what it refers to).
Overlap keeps a sentence or idea that straddles a boundary inside at
least one chunk. Chunks keep their source page number for citations.
"""

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def chunk_text(text, page, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split one page's text into overlapping chunks.

    Returns a list of dicts with keys: text, page.
    Tries to end a chunk at a sentence boundary ('. ') near the end of
    the window, falling back to a hard cut if none is found.
    """
    chunks = []
    if not text or not text.strip():
        return chunks
    text = " ".join(text.split())
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            window = text[start:end]
            # Prefer a sentence boundary in the last 140 chars of the window.
            cut = window.rfind(". ")
            if cut > len(window) - 140 and cut > 0:
                end = start + cut + 1
            else:
                # Otherwise break at a word boundary, never mid-word.
                space = window.rfind(" ")
                if space > 200:
                    end = start + space
        chunk = text[start:end].strip()
        if chunk:
            chunks.append({"text": chunk, "page": page})
        if end >= n:
            break
        # Next chunk overlaps, but starts at a word boundary: move to
        # the first space after the overlap point, then past it.
        overlap_start = end - overlap
        nxt = text.find(" ", overlap_start)
        start = nxt + 1 if nxt != -1 else end
        if start <= end - overlap:
            start = end
    return chunks


def chunk_pages(pages, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Chunk every page; assign a stable chunk id across the document."""
    chunks = []
    for page, text in pages:
        for chunk in chunk_text(text, page, chunk_size, overlap):
            chunk["id"] = len(chunks)
            chunks.append(chunk)
    return chunks
