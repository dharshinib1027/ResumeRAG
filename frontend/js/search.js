/**
 * Recruiter Semantic Search Page Logic with RAG Direct Answer Synthesis
 */

const API_BASE = "http://localhost:8000/api";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("searchForm");
  const input = document.getElementById("searchInput");

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (query) {
      executeSearch(query);
    }
  });

  const urlParams = new URLSearchParams(window.location.search);
  const qParam = urlParams.get("q");
  if (qParam) {
    input.value = qParam;
    executeSearch(qParam);
  }
});

function setQuery(text) {
  const input = document.getElementById("searchInput");
  input.value = text;
  executeSearch(text);
}

async function executeSearch(query) {
  const resultsGrid = document.getElementById("candidateResultsGrid");
  const resultsHeader = document.getElementById("resultsHeader");
  const countBadge = document.getElementById("resultsCountBadge");

  resultsHeader.style.display = "block";
  resultsGrid.innerHTML = `
    <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 2rem;">
      <i class="fa-solid fa-compass fa-spin" style="font-size: 3rem; color: var(--accent-primary); margin-bottom: 1rem;"></i>
      <h3 style="font-family: 'Outfit', sans-serif;">Synthesizing AI RAG Search Answer...</h3>
      <p style="color: var(--text-secondary); margin-top: 0.5rem;">Evaluating vector embeddings and keyword relevance for: "${escapeHtml(query)}"</p>
    </div>
  `;

  try {
    const resp = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query })
    });

    if (!resp.ok) {
      const errData = await resp.json();
      throw new Error(errData.detail || "Search failed");
    }

    const data = await resp.json();
    const candidates = data.results || [];
    const aiAnswer = data.ai_answer || "";

    countBadge.textContent = `${candidates.length} Candidate(s) Matched`;

    let html = "";

    // 1. Direct AI RAG Answer Banner
    if (aiAnswer) {
      html += `
        <div class="card" style="grid-column: 1 / -1; background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%); border: 1px solid var(--border-glow); margin-bottom: 1.5rem;">
          <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.6rem; color: var(--accent-cyan); font-weight: 700; font-size: 1.05rem;">
            <i class="fa-solid fa-wand-magic-sparkles"></i> AI Direct Search Answer
          </div>
          <div style="font-size: 1.05rem; line-height: 1.6; color: var(--text-primary); font-weight: 500;">
            ${formatMarkdownBold(escapeHtml(aiAnswer))}
          </div>
        </div>
      `;
    }

    if (candidates.length === 0) {
      html += `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-state-icon"><i class="fa-solid fa-folder-open"></i></div>
          <h3>No matching candidates found</h3>
          <p>Try broadening your query keywords or upload more candidate resumes to your database.</p>
        </div>
      `;
      resultsGrid.innerHTML = html;
      return;
    }

    // 2. Candidate Cards Grid
    candidates.forEach(cand => {
      const skillsHtml = (cand.skills || []).slice(0, 6).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join(" ");

      const excerpt = cand.top_excerpts && cand.top_excerpts.length > 0 
        ? escapeHtml(cand.top_excerpts[0])
        : "Matches candidate skills & profile context.";

      html += `
        <div class="candidate-card">
          <div>
            <div class="candidate-header">
              <div class="candidate-header-info">
                <h3 class="candidate-name">${escapeHtml(cand.candidate_name)}</h3>
                <div class="candidate-filename" title="${escapeHtml(cand.filename)}">
                  <i class="fa-solid fa-file-pdf"></i> ${escapeHtml(cand.filename)}
                </div>
              </div>
              <div class="match-badge">
                <i class="fa-solid fa-bolt"></i> ${cand.match_score}% Match
              </div>
            </div>

            <div style="margin-bottom: 1rem;">
              ${skillsHtml}
            </div>

            <div class="excerpt-box">
              <i class="fa-solid fa-quote-left" style="opacity: 0.5; margin-right: 0.4rem;"></i> 
              "${excerpt}"
            </div>
          </div>

          <div class="card-actions">
            <a href="candidate.html?id=${cand.candidate_id}" class="btn btn-secondary">
              <i class="fa-solid fa-address-card"></i> View Profile
            </a>
            <a href="interview.html?id=${cand.candidate_id}" class="btn btn-primary">
              <i class="fa-solid fa-clipboard-question"></i> Questions
            </a>
          </div>
        </div>
      `;
    });

    resultsGrid.innerHTML = html;

  } catch (err) {
    resultsGrid.innerHTML = `
      <div class="card" style="grid-column: 1 / -1; text-align: center; color: #fca5a5; padding: 3rem;">
        <i class="fa-solid fa-triangle-exclamation" style="font-size: 2.5rem; margin-bottom: 1rem;"></i>
        <h3>Search Error</h3>
        <p>${escapeHtml(err.message)}</p>
      </div>
    `;
  }
}

function formatMarkdownBold(text) {
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

function escapeHtml(str) {
  return String(str || '').replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  })[m]);
}
