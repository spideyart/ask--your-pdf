# ask-your-pdf — RAG Research Assistant

Upload a PDF, ask a question in plain English, and get an answer grounded
in that document, with citations to page and chunk, plus the source
passages. You can also generate quiz questions from the document.

**No API key. No paid service. No signup.** Everything runs locally after
a normal `pip install`. No external language-model API is used at any point.

## How to run (2 commands)

```bash
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000

## Deploy on Vercel

GitHub Pages cannot run this app — it only serves static files, and
this app needs a Python server for PDF extraction and TF-IDF retrieval.
Vercel can run it: `api/index.py` re-exports the Flask app, and
`vercel.json` routes all requests to it. Import the repository in
Vercel and deploy; no environment variables or API keys are needed.

Two Vercel limits to know for the demo: serverless requests are capped
at about 4.5 MB, so very large PDFs may be rejected before the app's
10 MB cap, and the in-memory index can be lost if Vercel cold-starts a
new function instance — if you ever see "Load a document first", just
load the sample (or re-upload) and ask again in the same session.

Try it without uploading anything first: click **Load sample document**,
then ask "How does Wi-Fi send data?" or "What weakens a Wi-Fi signal?"
Ask "What is the capital of France?" and you will get
"Not found in this document." — that is intentional, see below.

## What it does

- PDF upload (10 MB limit, `.pdf` only, safe filenames, no path traversal,
  uploaded content is never executed)
- Document indexing status (chunk count, document name)
- Question answering with citations (chunk id, page, similarity score)
- Source passages view, so you can check every answer yourself
- Quiz generation: fill-in-the-blank questions built from the document,
  with four options each, no language model
- Chat history for the running session
- Sample document included, so the demo works with no upload:
  `sample_docs/sample.txt` — "A Short Guide to Wi-Fi"

## Architecture (text diagram)

```
PDF file ──> pypdf text extraction ──> pages (page, text)
     │
     ├─ if < 50 characters of text: ScannedPDFError, clear message, no crash
     │
     ▼
Overlapping chunker ──> chunks (~500 chars, ~100 overlap, page kept)
     │
     ▼
TF-IDF index (scikit-learn) ──> chunk vectors
     │
Question ──> same TF-IDF vector ──> cosine similarity ──> top-5 chunks
     │
     ├─ best score < 0.15 ──> "Not found in this document."
     │
     └─ otherwise ──> extractive answer: top sentences from the
                     retrieved chunks, each with a citation
```

## How TF-IDF + cosine similarity works

TF-IDF turns each chunk into a vector of word weights. A word that
appears often in one chunk but rarely in the whole document gets a high
weight; a word that appears everywhere, like "the", gets a low weight.
The question is turned into the same kind of vector. Cosine similarity
measures the angle between the two vectors: 1.0 is the same direction,
0.0 is no shared words. The chunks with the highest scores are retrieved.

## How chunking and retrieval work

Chunking uses ~500 characters with ~100 characters of overlap. A chunk
much larger dilutes retrieval, because one chunk then covers several
unrelated ideas and matches a query only weakly. A chunk much smaller
loses context, because a sentence alone may not say what it refers to.
Overlap keeps an idea that straddles a boundary inside at least one chunk.
Each chunk keeps its page number, which is what makes citations possible.

Retrieval is top-5 by cosine similarity, then extractive answering:
sentences from the retrieved chunks are ranked by word overlap with the
question, and the top sentences are returned verbatim, cited. No new
claims are added.

## Anti-hallucination rule

If the best retrieved chunk scores below 0.15, the system answers
"Not found in this document." instead of inventing an answer. This is
tested: an out-of-document question (for example, about the capital of
France, when the document is about Wi-Fi) must return not-found, not a
plausible-sounding guess.

## How to test

```bash
pip install pytest
python -m pytest tests/ -v
```

Tests cover:

1. Chunking: long text splits into overlapping chunks, chunk ids are stable,
   empty text gives no chunks.
2. Retrieval: a known question returns the right chunk; a known question
   gets a cited answer; an out-of-document question returns not-found.
3. Quiz: questions have four options, a valid answer index, and a blank;
   the same seed gives the same quiz; an empty document gives no questions.

## Problems handled

- **Scanned / image-only PDFs:** detected by the low-text check in
  `rag/pdf_loader.py` and reported as a clear error, not a crash or an
  empty answer. OCR is listed under future work.
- **Chunk size:** ~500 / ~100 overlap, documented above, instead of
  whole-page chunks or single sentences.
- **Irrelevant retrieval / hallucination:** similarity threshold,
  extractive answers only, citations on every answer, not-found fallback.
- **Large PDFs / slow indexing:** 10 MB upload cap, indexing status is
  shown, the index is kept in memory for the running server, and the
  upload is deleted after extraction. Very large documents will still
  take longer to index — that is a real limit, see below.
- **Security:** `.pdf` only, 10 MB cap, `secure_filename`, no path
  traversal, no execution of uploaded content, no data sent to any
  external service.

## Limitations

- Retrieval is keyword-based TF-IDF, not semantic embeddings: a question
  phrased with completely different words from the document may score low
  even if it is about the same idea.
- Answers are extractive: the system can only repeat what the document
  says, it cannot summarise in its own words or reason across documents.
- Single document at a time, in-memory index only; restarting the server
  clears the loaded document.
- No OCR, so scanned PDFs are rejected rather than read.
- No voice narration and no multi-language support yet.

## Future work

- Local embeddings (for example, a small sentence-embedding model run
  locally) for semantic retrieval, still with no API key.
- Multi-document indexing and cross-document questions.
- OCR for scanned PDFs.
- Summarisation of a whole document from its chunks.
- Persistent index on disk, so a document survives a restart.

## Project structure

```
app.py                 Flask app, routes, upload limits, session state
rag/
  pdf_loader.py        pypdf extraction, scanned-PDF detection
  chunker.py           overlapping chunking, page-preserving
  retriever.py         TF-IDF index, cosine similarity, top-k
  answerer.py          extractive answers, citations, not-found rule
  quiz.py              keyword-based fill-in-the-blank quiz
templates/index.html   single page UI
static/style.css       styling
static/app.js          upload / ask / quiz / history client code
sample_docs/sample.txt sample document for the no-upload demo
tests/                 chunking, retrieval, quiz tests
requirements.txt       Flask, pypdf, scikit-learn (all free, open source)
```
