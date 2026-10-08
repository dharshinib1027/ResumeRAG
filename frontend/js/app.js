/* ResumeRAG frontend – single chatbot JS.
   Endpoints:
   GET /resumes                 -> [{ resume_id, name, filename, chunks }]
   POST /upload                 (multipart "files") -> { resumes: [...] } or { resume_id, name, filename }
   DELETE /resumes/{resume_id}  -> { status, resume_id }
   POST /chat                   { message, history, selected_resume_id }
                                -> { type, answer, candidates, sources, questions, selected_resume_id }
*/

const API_BASE = "http://localhost:8000";
const USE_MOCK = false; // Set true for offline UI testing

const state = {
  selectedResumeId: null,
  selectedCandidateName: null,
  resumes: [],
  history: [],
};

const $ = (id) => document.getElementById(id);

/* ---------- helpers ---------- */
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function toast(message) {
  const t = $("toast");
  t.textContent = message;
  t.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => t.classList.remove("show"), 3000);
}

async function api(path, options = {}) {
  if (USE_MOCK) return mockApi(path, options);
  const res = await fetch(API_BASE + path, options);
  if (!res.ok) {
    let detail = "";
    try {
      const body = await res.json();
      if (typeof body.detail === "string") {
        detail = body.detail;
      } else if (Array.isArray(body.detail)) {
        detail = body.detail.map((d) => d.msg || JSON.stringify(d)).join(", ");
      } else if (body.detail) {
        detail = JSON.stringify(body.detail);
      }
    } catch (_) {}
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json();
}

const postJSON = (path, body) =>
  api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

/* ---------- candidate selection state ---------- */
function setSelectedCandidate(resumeId, candidateName) {
  state.selectedResumeId = resumeId;
  state.selectedCandidateName = candidateName;

  const chip = $("candidate-chip");
  const nameEl = $("chip-candidate-name");

  if (resumeId && candidateName) {
    nameEl.textContent = candidateName;
    chip.style.display = "inline-flex";
  } else {
    chip.style.display = "none";
  }

  // Highlight selected in sidebar
  document.querySelectorAll(".resume-item").forEach((item) => {
    item.classList.toggle("selected", item.dataset.id === resumeId);
  });
}

$("chip-clear").addEventListener("click", () => setSelectedCandidate(null, null));

/* ---------- resumes list & upload ---------- */
async function loadResumes() {
  try {
    const list = await api("/resumes");
    state.resumes = list;
    renderResumesList();
  } catch (err) {
    console.error("Failed to load resumes:", err);
  }
}

function renderResumesList() {
  const container = $("resume-list");
  const countBadge = $("resumes-count");
  container.replaceChildren();
  countBadge.textContent = state.resumes.length;

  if (!state.resumes.length) {
    container.append(el("p", "empty-resumes", "No resumes uploaded yet."));
    return;
  }

  state.resumes.forEach((r) => {
    const item = el("div", "resume-item" + (r.resume_id === state.selectedResumeId ? " selected" : ""));
    item.dataset.id = r.resume_id;

    const info = el("div", "resume-info");
    info.append(el("div", "resume-name", r.name || r.filename));
    info.append(el("div", "resume-file", r.filename));

    const removeBtn = el("button", "btn-remove-resume", "×");
    removeBtn.title = "Delete resume";
    removeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteResume(r.resume_id);
    });

    item.append(info, removeBtn);

    item.addEventListener("click", () => {
      if (state.selectedResumeId === r.resume_id) {
        setSelectedCandidate(null, null);
      } else {
        setSelectedCandidate(r.resume_id, r.name || r.filename);
      }
    });

    container.append(item);
  });
}

async function uploadFiles(fileList) {
  if (!fileList || !fileList.length) return;
  const form = new FormData();
  Array.from(fileList).forEach((f) => form.append("files", f));

  toast(`Uploading ${fileList.length} file(s)...`);
  try {
    await api("/upload", { method: "POST", body: form });
    toast("Resumes uploaded and indexed!");
    await loadResumes();
  } catch (err) {
    toast("Upload failed: " + err.message);
  }
}

async function deleteResume(resumeId) {
  try {
    await api(`/resumes/${resumeId}`, { method: "DELETE" });
    toast("Resume deleted.");
    if (state.selectedResumeId === resumeId) {
      setSelectedCandidate(null, null);
    }
    await loadResumes();
  } catch (err) {
    toast("Failed to delete: " + err.message);
  }
}

$("file").addEventListener("change", (e) => uploadFiles(e.target.files));
const drop = $("drop");
["dragover", "dragenter"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => uploadFiles(e.dataTransfer.files));

/* ---------- chat interface ---------- */
const log = $("log");

function addMessage(kind, text) {
  $("chat-empty")?.remove();
  const msg = el("div", "msg " + kind);
  if (kind === "user") {
    msg.textContent = text;
  } else {
    msg.append(el("div", "answer", text));
  }
  log.append(msg);
  log.scrollTop = log.scrollHeight;
  return msg;
}

function renderChatResponse(msg, data) {
  msg.classList.remove("pending");
  const answerEl = msg.querySelector(".answer");
  answerEl.textContent = data.answer;

  // Update selected candidate if server returned one
  if (data.selected_resume_id) {
    const found = state.resumes.find((r) => r.resume_id === data.selected_resume_id);
    if (found) {
      setSelectedCandidate(found.resume_id, found.name || found.filename);
    }
  }

  // 1. Search results cards
  if (data.type === "search" && data.candidates && data.candidates.length) {
    const cardsWrap = el("div", "candidate-cards");
    data.candidates.forEach((c) => {
      const card = el("div", "cand-card");

      const head = el("div", "cand-card-head");
      head.append(el("h3", "cand-card-name", c.name || c.filename));
      head.append(el("span", "cand-card-score", Math.round(c.score * 100) + "% match"));

      const snip = el("p", "cand-card-snippet", c.snippet);

      const actions = el("div", "cand-card-actions");

      const askBtn = el("button", "btn-action", "Ask about candidate");
      askBtn.addEventListener("click", () => {
        setSelectedCandidate(c.resume_id, c.name || c.filename);
        ask(`Tell me more about ${c.name || c.filename}`);
      });

      const ivBtn = el("button", "btn-action", "Interview questions");
      ivBtn.addEventListener("click", () => {
        setSelectedCandidate(c.resume_id, c.name || c.filename);
        ask(`Generate 5 interview questions for ${c.name || c.filename}`);
      });

      actions.append(askBtn, ivBtn);
      card.append(head, snip, actions);
      cardsWrap.append(card);
    });
    msg.append(cardsWrap);
  }

  // 2. Sources for candidate_qa / compare
  if (data.sources && data.sources.length) {
    const details = el("details", "sources-details");
    const summary = el("summary", "sources-summary", `View Sources (${data.sources.length} excerpts)`);
    details.append(summary);

    const list = el("div", "sources-list");
    data.sources.forEach((s) => {
      const sc = el("div", "source-card");
      const candMeta = s.name ? `${s.name} – ` : "";
      const pageMeta = s.page ? `, page ${s.page}` : "";
      sc.append(el("div", "source-meta", `${candMeta}${s.section}${pageMeta}`));

      const p = el("p", "source-text");
      if (s.highlight && s.text.includes(s.highlight)) {
        const [before, after] = s.text.split(s.highlight, 2);
        p.append(before, el("mark", "", s.highlight), after);
      } else {
        p.textContent = s.text;
      }
      sc.append(p);
      list.append(sc);
    });
    details.append(list);
    msg.append(details);
  }

  // 3. Numbered Questions for interview
  if (data.type === "interview" && data.questions && data.questions.length) {
    const qList = el("ol", "questions-list");
    data.questions.forEach((q) => {
      const li = el("li", "question-item");
      li.append(document.createTextNode(q.question));
      if (q.section) {
        li.append(document.createElement("br"), el("span", "tag", q.section));
      }
      qList.append(li);
    });
    msg.append(qList);
  }
}

async function ask(messageText) {
  const text = messageText.trim();
  if (!text) return;

  addMessage("user", text);
  state.history.push({ role: "user", content: text });

  const botMsg = addMessage("bot pending", "Thinking...");

  try {
    const payload = {
      message: text,
      history: state.history.slice(-10),
      selected_resume_id: state.selectedResumeId,
    };
    const data = await postJSON("/chat", payload);

    renderChatResponse(botMsg, data);
    state.history.push({ role: "assistant", content: data.answer, candidates: data.candidates || [] });
  } catch (err) {
    botMsg.className = "msg bot error";
    botMsg.querySelector(".answer").textContent = "Error: " + err.message;
  }
  log.scrollTop = log.scrollHeight;
}

$("chat-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = $("question");
  const q = input.value.trim();
  if (!q) return;
  input.value = "";
  ask(q);
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => ask(chip.dataset.prompt || chip.textContent));
});

/* ---------- mock api handler ---------- */
async function mockApi(path) {
  await new Promise((r) => setTimeout(r, 600));
  if (path === "/resumes") {
    return [
      { resume_id: "demo1", name: "Jane Doe", filename: "Jane_Doe_Resume.pdf", chunks: 5 },
      { resume_id: "demo2", name: "John Smith", filename: "John_Smith_Resume.docx", chunks: 4 },
    ];
  }
  if (path === "/chat") {
    return {
      type: "search",
      answer: "Found 2 matching candidates:",
      candidates: [
        { resume_id: "demo1", name: "Jane Doe", filename: "Jane_Doe_Resume.pdf", score: 0.92, snippet: "Senior NLP engineer with PyTorch and Python experience." },
      ],
      sources: [],
      questions: [],
      selected_resume_id: "demo1",
    };
  }
  return {};
}

// Initial load
loadResumes();
