"""TF-IDF retrieval with cosine similarity. No external API, no model download.

How it works: each chunk becomes a vector of word weights. TF-IDF
(term frequency x inverse document frequency) gives a high weight to
words that are frequent in one chunk but rare across the document, and
a low weight to common words such as "the". A question is turned into
the same kind of vector, and cosine similarity measures the angle
between the question vector and each chunk vector: 1.0 means identical
direction, 0.0 means no shared words. The highest-scoring chunks win.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), max_features=5000
        )
        self.matrix = None
        if chunks:
            self.matrix = self.vectorizer.fit_transform(
                [c["text"] for c in chunks]
            )

    def search(self, query, top_k=5):
        """Return top_k chunks as dicts with a similarity score, sorted desc."""
        if not query or not query.strip() or self.matrix is None:
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix)[0]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked[:top_k]:
            chunk = dict(self.chunks[i])
            chunk["score"] = float(scores[i])
            results.append(chunk)
        return results
