"""Keyword-based quiz generation. No language model is used.

Method: for a chunk, pick its most distinctive word (long, alphabetic,
appearing in that chunk) as the blanked answer, blank it out of a
sentence containing it, and use three other distinctive words from
other chunks as distractors. Questions are deterministic for a given
document and seed, so a teacher can re-run them and get the same quiz.
"""

import random
import re


def _distinctive_words(text, stopwords=None):
    stopwords = stopwords or {
        "the", "and", "that", "with", "from", "this", "which", "have",
        "were", "are", "was", "for", "not", "but", "they", "their",
        "when", "into", "about", "after", "before", "during",
    }
    words = re.findall(r"[A-Za-z]{5,}", text)
    seen = []
    for word in words:
        low = word.lower()
        if low not in stopwords and low not in seen:
            seen.append(low)
    return seen


def generate_quiz(chunks, num_questions=5, seed=42):
    """Return a list of {"question", "options", "answer_index", "page"}."""
    rng = random.Random(seed)
    if not chunks:
        return []
    all_words = []
    for chunk in chunks:
        all_words.extend(_distinctive_words(chunk["text"]))
    # Preserve order, de-duplicate.
    all_words = list(dict.fromkeys(all_words))
    questions = []
    pool = list(chunks)
    rng.shuffle(pool)
    for chunk in pool:
        if len(questions) >= num_questions:
            break
        words = _distinctive_words(chunk["text"])
        if not words:
            continue
        answer = words[0]
        # Only use a sentence that starts cleanly (capital letter) and
        # contains the answer as a whole word, never a word fragment.
        sentences = []
        for s in chunk["text"].split(". "):
            s = s.strip()
            if len(s) > 20 and s[0].isupper() and re.search(r"\b" + re.escape(answer) + r"\b", s, re.IGNORECASE):
                sentences.append(s)
        if not sentences:
            continue
        sentence = sentences[0].strip()
        blanked = re.sub(r"\b" + re.escape(answer) + r"\b", "______", sentence, flags=re.IGNORECASE, count=1)
        distractors = [w for w in all_words if w != answer]
        rng.shuffle(distractors)
        options = [answer] + distractors[:3]
        if len(options) < 4:
            continue
        rng.shuffle(options)
        questions.append(
            {
                "question": f"Fill in the blank: {blanked}",
                "options": options,
                "answer_index": options.index(answer),
                "page": chunk["page"],
            }
        )
    return questions
