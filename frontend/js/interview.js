/**
 * Interview Question Generator Logic
 */

const API_BASE = "http://localhost:8000/api";
let currentInterviewData = null;

document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const candidateId = urlParams.get("id");

  if (!candidateId) {
    document.getElementById("questionsContainer").innerHTML = `
      <div class="card" style="text-align: center; color: #fca5a5; padding: 3rem;">
        <h2>Candidate ID Missing</h2>
        <p><a href="search.html" style="color: var(--accent-cyan); text-decoration: underline;">Return to Search</a></p>
      </div>
    `;
    return;
  }

  fetchInterviewQuestions(candidateId);
});

async function fetchInterviewQuestions(candidateId) {
  const headerContainer = document.getElementById("interviewCandidateHeader");
  const questionsContainer = document.getElementById("questionsContainer");

  try {
    const resp = await fetch(`${API_BASE}/interview/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ candidate_id: candidateId })
    });

    if (!resp.ok) {
      const errData = await resp.json();
      throw new Error(errData.detail || "Question generation failed");
    }

    const data = await resp.json();
    currentInterviewData = data;

    // Render Banner Header
    headerContainer.innerHTML = `
      <div class="profile-banner">
        <div>
          <h1 class="profile-name">Interview Guide: ${escapeHtml(data.candidate_name)}</h1>
          <div class="profile-meta-list">
            <div class="meta-item"><i class="fa-solid fa-file-pdf"></i> ${escapeHtml(data.filename)}</div>
            <div class="meta-item"><i class="fa-solid fa-wand-magic-sparkles"></i> Engine: ${escapeHtml(data.generated_via)}</div>
            <div class="meta-item"><i class="fa-solid fa-shield-halved"></i> 100% Resume Grounded</div>
          </div>
        </div>
        <div>
          <a href="candidate.html?id=${data.candidate_id}" class="btn btn-secondary">
            <i class="fa-solid fa-user"></i> View Profile
          </a>
        </div>
      </div>
    `;

    const qObj = data.questions || {};
    const techQs = qObj.technical || [];
    const projQs = qObj.project_based || [];
    const behQs = qObj.behavioral || [];

    let html = "";

    // 1. Technical Questions
    if (techQs.length > 0) {
      html += `
        <div class="question-category-title">
          <i class="fa-solid fa-code" style="color: var(--accent-primary);"></i> Technical & Tools Questions
          <span class="badge">${techQs.length} Questions</span>
        </div>
      `;
      techQs.forEach((q, idx) => {
        html += renderQuestionCard(q, idx + 1, "Tech");
      });
    }

    // 2. Project-Based Questions
    if (projQs.length > 0) {
      html += `
        <div class="question-category-title">
          <i class="fa-solid fa-diagram-project" style="color: var(--accent-cyan);"></i> Project-Based & Architecture Questions
          <span class="badge">${projQs.length} Questions</span>
        </div>
      `;
      projQs.forEach((q, idx) => {
        html += renderQuestionCard(q, idx + 1, "Project");
      });
    }

    // 3. Behavioral Questions
    if (behQs.length > 0) {
      html += `
        <div class="question-category-title">
          <i class="fa-solid fa-comments" style="color: var(--accent-emerald);"></i> Behavioral & Experience Questions
          <span class="badge">${behQs.length} Questions</span>
        </div>
      `;
      behQs.forEach((q, idx) => {
        html += renderQuestionCard(q, idx + 1, "Behavioral");
      });
    }

    if (!html) {
      html = `<p style="text-align: center; color: var(--text-muted); padding: 3rem;">No interview questions could be generated.</p>`;
    }

    questionsContainer.innerHTML = html;

  } catch (err) {
    questionsContainer.innerHTML = `
      <div class="card" style="text-align: center; color: #fca5a5; padding: 3rem;">
        <i class="fa-solid fa-circle-exclamation" style="font-size: 2.5rem; margin-bottom: 1rem;"></i>
        <h3>Interview Generation Failed</h3>
        <p>${escapeHtml(err.message)}</p>
      </div>
    `;
  }
}

function renderQuestionCard(q, index, categoryTag) {
  const diff = (q.difficulty || "Medium").toLowerCase();
  const diffClass = diff === "easy" ? "difficulty-easy" : (diff === "hard" ? "difficulty-hard" : "difficulty-medium");

  return `
    <div class="question-card">
      <div class="question-header">
        <span style="font-size: 0.8rem; font-weight: 700; color: var(--accent-primary); text-transform: uppercase;">
          ${categoryTag} Q#${index}
        </span>
        <span class="difficulty-badge ${diffClass}">${escapeHtml(q.difficulty || 'Medium')}</span>
      </div>

      <div class="question-text">${escapeHtml(q.question)}</div>

      ${q.grounding_context ? `
        <div class="grounding-box">
          <i class="fa-solid fa-pin" style="margin-right: 0.4rem;"></i>
          <strong>Grounded in Resume:</strong> "${escapeHtml(q.grounding_context)}"
        </div>
      ` : ''}

      ${q.what_to_look_for ? `
        <div class="look-for-box">
          <strong style="color: var(--text-primary);"><i class="fa-solid fa-magnifying-glass"></i> What to evaluate in answer:</strong> ${escapeHtml(q.what_to_look_for)}
        </div>
      ` : ''}
    </div>
  `;
}

function copyAllQuestions() {
  if (!currentInterviewData || !currentInterviewData.questions) {
    alert("No questions loaded to copy.");
    return;
  }

  const qObj = currentInterviewData.questions;
  let text = `INTERVIEW QUESTIONS FOR ${currentInterviewData.candidate_name.toUpperCase()}\n`;
  text += `Resume File: ${currentInterviewData.filename}\n`;
  text += `=====================================================\n\n`;

  const categories = [
    { title: "TECHNICAL QUESTIONS", items: qObj.technical || [] },
    { title: "PROJECT-BASED QUESTIONS", items: qObj.project_based || [] },
    { title: "BEHAVIORAL QUESTIONS", items: qObj.behavioral || [] }
  ];

  categories.forEach(c => {
    if (c.items.length > 0) {
      text += `--- ${c.title} ---\n`;
      c.items.forEach((q, idx) => {
        text += `${idx + 1}. ${q.question} [Difficulty: ${q.difficulty}]\n`;
        if (q.grounding_context) text += `   Grounded in: ${q.grounding_context}\n`;
        if (q.what_to_look_for) text += `   Look for: ${q.what_to_look_for}\n`;
        text += `\n`;
      });
    }
  });

  navigator.clipboard.writeText(text).then(() => {
    alert("Copied all grounded interview questions to clipboard!");
  }).catch(err => {
    console.error("Failed to copy:", err);
  });
}

function escapeHtml(str) {
  return String(str || '').replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  })[m]);
}
