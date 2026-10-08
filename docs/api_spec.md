# ResumeRAG API

Base URL: `http://localhost:8000` · Interactive docs: `/docs`

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/health` | none | `{ status, llm_enabled }` |
| GET | `/resumes` | none | `[{ resume_id, name, filename, chunks }]` |
| DELETE | `/resumes/{resume_id}` | none | `{ status: "deleted", resume_id }` |
| POST | `/upload` | multipart `file` or `files` (PDF/DOCX, max 10 MB) | `{ resume_id, name, filename, chunks }` or `{ resumes: [...] }` |
| POST | `/chat` | `{ message, history: [...], selected_resume_id }` | `{ type, answer, candidates: [...], sources: [...], questions: [...], selected_resume_id }` |

### Chat Response Types

- `search`: returns ranked candidate cards `[{ resume_id, name, filename, score, snippet }]`.
- `candidate_qa`: returns grounded answer and collapsible sources `[{ resume_id, name, section, page, text, highlight }]`.
- `interview`: returns generated/template interview questions `[{ question, section }]`.
- `compare`: returns side-by-side candidate comparison and grounded sources from both candidates.
- `general`: returns helpful assistant response.

### Errors & Fallbacks

Errors return `{ "detail": "message" }` with status 400 (bad file type / missing file), 404 (not found), 413 (file too large) or 422 (unreadable file).

An active `GEMINI_API_KEY` is strictly required for AI answer synthesis and candidate interview question generation. If `GEMINI_API_KEY` is missing or invalid, the API returns a 500 status error with a detail message indicating that an active Gemini API key is required.
