/**
 * Candidate Profile Details Logic
 */

const API_BASE = "http://localhost:8000/api";

document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const candId = urlParams.get("id");

  if (!candId) {
    document.getElementById("profileHeaderContainer").innerHTML = `
      <div class="card" style="text-align: center; padding: 3rem; color: #fca5a5;">
        <h2>Candidate ID missing</h2>
        <p><a href="search.html" style="color: var(--accent-cyan); text-decoration: underline;">Return to Search</a></p>
      </div>
    `;
    return;
  }

  loadCandidateDetails(candId);
});

async function loadCandidateDetails(candidateId) {
  const headerContainer = document.getElementById("profileHeaderContainer");
  const sectionsContainer = document.getElementById("profileSectionsContainer");

  try {
    const resp = await fetch(`${API_BASE}/candidate/${candidateId}`);
    if (!resp.ok) {
      throw new Error(`Candidate '${candidateId}' not found.`);
    }

    const cand = await resp.json();
    document.title = `${cand.candidate_name} – Profile Details`;

    // Render Banner Header
    const email = cand.contact_info?.email || "Not specified";
    const phone = cand.contact_info?.phone || "Not specified";
    const linkedin = cand.contact_info?.linkedin || "";
    const github = cand.contact_info?.github || "";

    headerContainer.innerHTML = `
      <div class="profile-banner">
        <div>
          <h1 class="profile-name">${escapeHtml(cand.candidate_name)}</h1>
          <div class="profile-meta-list">
            <div class="meta-item"><i class="fa-solid fa-envelope"></i> ${escapeHtml(email)}</div>
            ${phone !== "Not specified" ? `<div class="meta-item"><i class="fa-solid fa-phone"></i> ${escapeHtml(phone)}</div>` : ''}
            <div class="meta-item"><i class="fa-solid fa-file-pdf"></i> ${escapeHtml(cand.filename)}</div>
            ${linkedin ? `<div class="meta-item"><i class="fa-brands fa-linkedin"></i> ${escapeHtml(linkedin)}</div>` : ''}
            ${github ? `<div class="meta-item"><i class="fa-brands fa-github"></i> ${escapeHtml(github)}</div>` : ''}
          </div>
        </div>
        <div>
          <a href="interview.html?id=${cand.candidate_id}" class="btn btn-primary" style="font-size: 1rem; padding: 0.9rem 1.6rem;">
            <i class="fa-solid fa-clipboard-question"></i> Generate Interview Questions
          </a>
        </div>
      </div>
    `;

    // Render Profile Sections
    let sectionsHtml = "";

    // Skills section
    if (cand.skills && cand.skills.length > 0) {
      const tags = cand.skills.map(s => `<span class="skill-tag" style="font-size: 0.9rem; padding: 0.4rem 0.9rem;">${escapeHtml(s)}</span>`).join(" ");
      sectionsHtml += `
        <div class="profile-section-box">
          <div class="section-title"><i class="fa-solid fa-code"></i> Skills & Key Competencies</div>
          <div>${tags}</div>
        </div>
      `;
    }

    const secDict = cand.section_dict || {};

    const secMap = [
      { key: "summary", title: "Professional Summary & Objective", icon: "fa-regular fa-id-card" },
      { key: "experience", title: "Work Experience & History", icon: "fa-solid fa-briefcase" },
      { key: "projects", title: "Projects & Implementations", icon: "fa-solid fa-diagram-project" },
      { key: "education", title: "Education & Qualifications", icon: "fa-solid fa-graduation-cap" },
      { key: "certifications", title: "Certifications & Achievements", icon: "fa-solid fa-award" }
    ];

    secMap.forEach(s => {
      const text = secDict[s.key];
      if (text && text.trim()) {
        sectionsHtml += `
          <div class="profile-section-box">
            <div class="section-title"><i class="${s.icon}"></i> ${s.title}</div>
            <div class="text-content-block">${escapeHtml(text)}</div>
          </div>
        `;
      }
    });

    // Fallback full text if sections were sparse
    if (!sectionsHtml) {
      sectionsHtml = `
        <div class="profile-section-box">
          <div class="section-title"><i class="fa-solid fa-file-alt"></i> Resume Extracted Text</div>
          <div class="text-content-block">${escapeHtml(cand.full_text || "No text available")}</div>
        </div>
      `;
    }

    sectionsContainer.innerHTML = sectionsHtml;

  } catch (err) {
    headerContainer.innerHTML = `
      <div class="card" style="text-align: center; color: #fca5a5; padding: 3rem;">
        <i class="fa-solid fa-circle-exclamation" style="font-size: 2.5rem; margin-bottom: 1rem;"></i>
        <h3>Error Loading Candidate Details</h3>
        <p>${escapeHtml(err.message)}</p>
      </div>
    `;
  }
}

function escapeHtml(str) {
  return String(str || '').replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  })[m]);
}
