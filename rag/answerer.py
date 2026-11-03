"""Extractive answering with citations and a not-found fallback.

This is deliberately extractive, not generative: the answer is made of
sentences taken verbatim from the retrieved chunks, each with a
citation to its chunk and page. No new claims are invented.

Anti-hallucination rule: if the best retrieved chunk scores below
SIMILARITY_THRESHOLD, the answer is "Not found in this document."
instead of a guess. That threshold is the single most important
safety control in this project.
"""

import re

SIMILARITY_THRESHOLD = 0.15
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text):
    return [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]


def answer_question(query, retrieved, threshold=SIMILARITY_THRESHOLD, max_sentences=4):
    """Return (answer_text, citations, sources).

    citations: list of {"chunk_id", "page", "score"}
    sources: the retrieved chunks used, in score order.
    """
    if not retrieved or retrieved[0]["score"] < threshold:
        return (
            "Not found in this document.",
            [],
            retrieved,
        )
    # Score sentences by word overlap with the query, preferring
    # sentences from higher-ranked chunks.
    query_words = set(re.findall(r"[a-z0-9]+", query.lower()))
    scored = []
    for rank, chunk in enumerate(retrieved):
        if chunk["score"] < threshold:
            continue
        for sentence in split_sentences(chunk["text"]):
            words = set(re.findall(r"[a-z0-9]+", sentence.lower()))
            overlap = len(query_words & words)
            if overlap:
                scored.append((overlap - rank * 0.1, sentence, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    picked = []
    used_chunks = []
    for _score, sentence, chunk in scored:
        if sentence not in picked:
            picked.append(sentence)
        if chunk["id"] not in [c["chunk_id"] for c in used_chunks]:
            used_chunks.append(
                {"chunk_id": chunk["id"], "page": chunk["page"], "score": chunk["score"]}
            )
        if len(picked) >= max_sentences:
            break
    if not picked:
        # Fallback: use the top chunk verbatim, still cited.
        top = retrieved[0]
        picked = split_sentences(top["text"])[:max_sentences]
        used_chunks = [
            {"chunk_id": top["id"], "page": top["page"], "score": top["score"]}
        ]
    answer = " ".join(picked)
    return answer, used_chunks, retrieved
