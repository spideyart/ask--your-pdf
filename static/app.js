async function refreshStatus() {
  const res = await fetch("/status");
  const data = await res.json();
  document.getElementById("status").textContent = data.status;
  const history = document.getElementById("history");
  history.innerHTML = data.history.map(
    (h) => `<li><b>${escapeHtml(h.question)}</b> — ${escapeHtml(h.answer)}</li>`
  ).join("");
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
document.getElementById("upload-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = document.getElementById("file").files[0];
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/upload", { method: "POST", body: form });
  const data = await res.json();
  document.getElementById("status").textContent = data.status || data.error || "Upload failed.";
  refreshStatus();
});
document.getElementById("sample-btn").addEventListener("click", async () => {
  const res = await fetch("/sample", { method: "POST" });
  const data = await res.json();
  document.getElementById("status").textContent = data.status || data.error || "Sample failed.";
  refreshStatus();
});
document.getElementById("ask-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = document.getElementById("question").value;
  const res = await fetch("/ask", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ question }) });
  const data = await res.json();
  if (data.error) { document.getElementById("answer").textContent = data.error; return; }
  document.getElementById("answer").textContent = data.answer;
  document.getElementById("citations").textContent = data.citations.length
    ? "Citations: " + data.citations.map((c) => `chunk ${c.chunk_id}, page ${c.page} (score ${c.score.toFixed(3)})`).join("; ")
    : "No citations — this question was not found in the document.";
  const box = document.getElementById("sources-box");
  box.hidden = false;
  document.getElementById("sources").innerHTML = data.sources.map(
    (s) => `<div class="source"><span class="score">chunk ${s.chunk_id}, page ${s.page}, score ${s.score}</span><br>${escapeHtml(s.text)}</div>`
  ).join("");
  refreshStatus();
});
document.getElementById("quiz-btn").addEventListener("click", async () => {
  const res = await fetch("/quiz");
  const data = await res.json();
  if (data.error) { document.getElementById("quiz").textContent = data.error; return; }
  document.getElementById("quiz").innerHTML = data.questions.map((q, i) => `
    <div class="source"><b>Q${i + 1}.</b> ${escapeHtml(q.question)}<br>
    ${q.options.map((o, j) => `<label><input type="radio" name="q${i}" value="${j}"> ${escapeHtml(o)}</label><br>`).join("")}
    <small>Answer: ${escapeHtml(q.options[q.answer_index])} (page ${q.page})</small></div>
  `).join("");
});
refreshStatus();
