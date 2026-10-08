/**
 * Upload Page Logic & Stats Dashboard
 */

const API_BASE = "http://localhost:8000/api";

document.addEventListener("DOMContentLoaded", () => {
  loadStats();
  loadResumes();
  setupDropzone();
});

// Load stats overview
async function loadStats() {
  try {
    const resp = await fetch(`${API_BASE}/stats`);
    if (!resp.ok) return;
    const data = await resp.json();

    document.getElementById("statResumes").textContent = data.total_resumes || 0;
    document.getElementById("statCandidates").textContent = data.total_candidates || 0;
    document.getElementById("statSkills").textContent = data.total_unique_skills || 0;
    document.getElementById("statChunks").textContent = data.total_vector_chunks || 0;
  } catch (err) {
    console.error("Failed to load dashboard stats:", err);
  }
}

// Load uploaded candidates table
async function loadResumes() {
  const container = document.getElementById("candidatesListTable");
  try {
    const resp = await fetch(`${API_BASE}/resumes`);
    if (!resp.ok) throw new Error("Failed to fetch candidates database");
    const candidates = await resp.json();

    if (!candidates || candidates.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
          <i class="fa-solid fa-folder-open" style="font-size: 2.5rem; margin-bottom: 0.8rem; opacity: 0.4;"></i>
          <p>No candidate resumes uploaded yet.</p>
          <p style="font-size: 0.85rem;">Drag & drop PDF resumes above to start building your database.</p>
        </div>
      `;
      return;
    }

    let html = `
      <table class="resume-table">
        <thead>
          <tr>
            <th>Candidate Name</th>
            <th>Resume File</th>
            <th>Extracted Skills</th>
            <th>Vector Chunks</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
    `;

    candidates.forEach(cand => {
      const skillsHtml = (cand.skills || []).slice(0, 5).map(s => `<span class="skill-tag">${s}</span>`).join(" ");
      const moreSkills = (cand.skills || []).length > 5 ? `<span style="font-size: 0.75rem; color: var(--text-muted);">+${cand.skills.length - 5} more</span>` : "";

      html += `
        <tr>
          <td>
            <div style="font-weight: 700; color: var(--text-primary);">${escapeHtml(cand.candidate_name)}</div>
            <div style="font-size: 0.8rem; color: var(--text-muted);">${cand.contact_info?.email || 'No email extracted'}</div>
          </td>
          <td style="font-size: 0.9rem; color: var(--text-secondary);">${escapeHtml(cand.filename)}</td>
          <td>${skillsHtml} ${moreSkills}</td>
          <td><span class="skill-tag" style="background: rgba(6, 182, 212, 0.15); color: var(--accent-cyan); border-color: rgba(6, 182, 212, 0.3);">${cand.chunk_count} chunks</span></td>
          <td>
            <div style="display: flex; gap: 0.5rem;">
              <a href="candidate.html?id=${cand.candidate_id}" class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                <i class="fa-solid fa-eye"></i> View
              </a>
              <a href="interview.html?id=${cand.candidate_id}" class="btn btn-primary" style="font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                <i class="fa-solid fa-clipboard-question"></i> Questions
              </a>
              <button onclick="deleteResume('${cand.candidate_id}')" class="btn btn-danger" style="font-size: 0.8rem; padding: 0.4rem 0.6rem;">
                <i class="fa-solid fa-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<p style="color: #fca5a5; text-align: center;">Error loading resumes: ${err.message}</p>`;
  }
}

// Drag & Drop Setup
function setupDropzone() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");

  ["dragenter", "dragover"].forEach(evtName => {
    dropzone.addEventListener(evtName, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    }, false);
  });

  ["dragleave", "drop"].forEach(evtName => {
    dropzone.addEventListener(evtName, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    }, false);
  });

  dropzone.addEventListener("drop", (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      handleFilesUpload(files);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFilesUpload(e.target.files);
    }
  });
}

// Upload Files Handler
async function handleFilesUpload(files) {
  const progressContainer = document.getElementById("progressContainer");
  const progressBarFill = document.getElementById("progressBarFill");
  const statusMsg = document.getElementById("uploadStatusMessage");

  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  progressContainer.style.display = "block";
  progressBarFill.style.width = "40%";
  statusMsg.textContent = `Uploading and parsing ${files.length} resume(s)...`;

  try {
    const resp = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData
    });

    progressBarFill.style.width = "80%";

    if (!resp.ok) {
      const errData = await resp.json();
      throw new Error(errData.detail || "Upload failed");
    }

    const data = await resp.json();
    progressBarFill.style.width = "100%";
    statusMsg.textContent = `Successfully processed ${data.uploaded_count} resume(s)!`;

    setTimeout(() => {
      progressContainer.style.display = "none";
      progressBarFill.style.width = "0%";
      statusMsg.textContent = "";
    }, 3000);

    loadStats();
    loadResumes();
  } catch (err) {
    progressContainer.style.display = "none";
    statusMsg.textContent = `Error: ${err.message}`;
    statusMsg.style.color = "#fca5a5";
  }
}

// Delete Candidate
async function deleteResume(candidateId) {
  if (!confirm("Are you sure you want to delete this candidate profile and its vector index?")) return;

  try {
    const resp = await fetch(`${API_BASE}/resumes/${candidateId}`, { method: "DELETE" });
    if (!resp.ok) throw new Error("Delete failed");
    loadStats();
    loadResumes();
  } catch (err) {
    alert(`Could not delete candidate: ${err.message}`);
  }
}

function escapeHtml(str) {
  return String(str || '').replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  })[m]);
}
