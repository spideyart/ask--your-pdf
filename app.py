"""ask-your-pdf: offline RAG research assistant.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000

No API key, no external service, no signup. Everything runs locally.
The index is kept in memory for the running server only; restarting
the server clears it. Uploaded files are never executed and are only
read as PDF text.
"""

import os
import tempfile

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from rag.answerer import answer_question
from rag.chunker import chunk_pages
from rag.pdf_loader import ScannedPDFError, extract_pages, pages_to_text
from rag.quiz import generate_quiz
from rag.retriever import Retriever

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload cap
ALLOWED_EXTENSIONS = {"pdf"}
SAMPLE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "sample_docs", "sample.txt"
)

# In-memory state for the running server. This keeps the demo simple
# and avoids storing user documents on disk after indexing.
STATE = {
    "document_name": None,
    "chunks": [],
    "retriever": None,
    "history": [],
    "status": "No document loaded yet. Upload a PDF, or load the sample.",
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def index_chunks(document_name, chunks):
    STATE["document_name"] = document_name
    STATE["chunks"] = chunks
    STATE["retriever"] = Retriever(chunks)
    STATE["history"] = []
    STATE["status"] = (
        f"Indexed {document_name}: {len(chunks)} chunks ready. Ask a question."
    )


def index_text_document(document_name, text):
    chunks = chunk_pages([(1, text)])
    index_chunks(document_name, chunks)
    return len(chunks)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/status")
def status():
    return jsonify(
        {
            "document_name": STATE["document_name"],
            "chunk_count": len(STATE["chunks"]),
            "status": STATE["status"],
            "history": STATE["history"][-20:],
        }
    )


@app.route("/sample", methods=["POST"])
def load_sample():
    try:
        with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return jsonify({"error": "Sample document is missing."}), 500
    count = index_text_document("sample.txt — A Short Guide to Wi-Fi", text)
    return jsonify({"status": STATE["status"], "chunk_count": count})


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file was uploaded."}), 400
    uploaded = request.files["file"]
    if not uploaded.filename:
        return jsonify({"error": "No file was selected."}), 400
    if not allowed_file(uploaded.filename):
        return jsonify({"error": "Only .pdf files are accepted."}), 400
    safe_name = secure_filename(uploaded.filename)
    if not safe_name:
        return jsonify({"error": "That filename is not usable."}), 400
    # Save to a temporary file only for extraction, then delete it.
    # Uploaded content is never executed.
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    try:
        uploaded.save(tmp.name)
        tmp.close()
        try:
            pages = pages_to_text(extract_pages(tmp.name))
        except ScannedPDFError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception:
            return jsonify({"error": "Could not read this PDF. It may be damaged."}), 400
        chunks = chunk_pages(pages)
        if not chunks:
            return jsonify({"error": "No usable text was found in this PDF."}), 400
        index_chunks(safe_name, chunks)
        return jsonify({"status": STATE["status"], "chunk_count": len(chunks)})
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Please type a question."}), 400
    if STATE["retriever"] is None:
        return jsonify({"error": "Load a document first: upload a PDF or load the sample."}), 400
    retrieved = STATE["retriever"].search(question, top_k=5)
    answer, citations, _sources = answer_question(question, retrieved)
    STATE["history"].append({"question": question, "answer": answer})
    sources = [
        {"chunk_id": c["id"], "page": c["page"], "score": round(c["score"], 3), "text": c["text"]}
        for c in retrieved
    ]
    return jsonify({"answer": answer, "citations": citations, "sources": sources})


@app.route("/quiz")
def quiz():
    if not STATE["chunks"]:
        return jsonify({"error": "Load a document first."}), 400
    questions = generate_quiz(STATE["chunks"], num_questions=5)
    return jsonify({"questions": questions})


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "File is too large. The limit is 10 MB."}), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
