import unittest

from rag.chunker import chunk_pages, chunk_text


class TestChunker(unittest.TestCase):
    def test_chunking_splits_long_text_with_overlap(self):
        text = " ".join(f"Sentence number {i} about Wi-Fi routers and signals." for i in range(40))
        chunks = chunk_text(text, page=1)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk["text"]), 520)
            self.assertEqual(chunk["page"], 1)

    def test_chunk_ids_are_stable(self):
        chunks = chunk_pages([(1, "Wi-Fi " * 200), (2, "Routers " * 200)])
        ids = [c["id"] for c in chunks]
        self.assertEqual(ids, list(range(len(chunks))))

    def test_empty_text_gives_no_chunks(self):
        self.assertEqual(chunk_text("", page=1), [])
        self.assertEqual(chunk_text("   ", page=1), [])


if __name__ == "__main__":
    unittest.main()
