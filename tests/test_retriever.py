import unittest

from rag.answerer import answer_question
from rag.chunker import chunk_pages
from rag.retriever import Retriever

TEXT = (
    "Wi-Fi is a wireless networking technology that lets devices connect "
    "to the internet without cables. A Wi-Fi router broadcasts radio waves. "
    "Photosynthesis is how green plants use sunlight, water, and carbon "
    "dioxide to make food and release oxygen."
)


class TestRetriever(unittest.TestCase):
    def setUp(self):
        self.chunks = chunk_pages([(1, TEXT * 3)])
        self.retriever = Retriever(self.chunks)

    def test_retrieval_returns_right_chunk_for_known_question(self):
        results = self.retriever.search("How does Wi-Fi send data without cables?", top_k=3)
        self.assertTrue(results)
        self.assertIn("Wi-Fi", results[0]["text"])
        self.assertGreater(results[0]["score"], 0.1)

    def test_low_similarity_returns_not_found(self):
        results = self.retriever.search("What is the capital city of France?", top_k=5)
        answer, citations, _ = answer_question("What is the capital city of France?", results)
        self.assertEqual(answer, "Not found in this document.")
        self.assertEqual(citations, [])

    def test_known_question_gets_cited_answer(self):
        results = self.retriever.search("What does a Wi-Fi router broadcast?", top_k=5)
        answer, citations, _ = answer_question("What does a Wi-Fi router broadcast?", results)
        self.assertNotEqual(answer, "Not found in this document.")
        self.assertTrue(citations)
        self.assertIn("radio", answer.lower())


if __name__ == "__main__":
    unittest.main()
