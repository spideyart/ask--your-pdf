import unittest

from rag.chunker import chunk_pages
from rag.quiz import generate_quiz

TEXT = (
    "Wi-Fi routers broadcast radio waves that carry data packets to phones "
    "and laptops. Walls and distance weaken the wireless signal, so a device "
    "close to the router usually gets a faster connection. Networks are "
    "identified by an SSID name and protected by a password."
)


class TestQuiz(unittest.TestCase):
    def test_quiz_generates_questions_with_four_options(self):
        chunks = chunk_pages([(1, TEXT * 3)])
        questions = generate_quiz(chunks, num_questions=3)
        self.assertTrue(questions)
        for q in questions:
            self.assertEqual(len(q["options"]), 4)
            self.assertIn(q["answer_index"], range(4))
            self.assertIn("______", q["question"])

    def test_quiz_is_deterministic(self):
        chunks = chunk_pages([(1, TEXT * 3)])
        first = generate_quiz(chunks, num_questions=3, seed=42)
        second = generate_quiz(chunks, num_questions=3, seed=42)
        self.assertEqual(first, second)

    def test_quiz_empty_document(self):
        self.assertEqual(generate_quiz([]), [])


if __name__ == "__main__":
    unittest.main()
