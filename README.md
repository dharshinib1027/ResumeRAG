# ResumeRAG – AI-Powered Resume Intelligence System

A RAG-based recruitment assistant that allows recruiters to upload multiple candidate resumes (PDF/DOCX), perform natural-language semantic searches across candidate profiles, inspect detailed extracted resume metadata, and generate personalized, resume-grounded interview questions.

---

## 🌟 Key Features

1. **Multi-Resume Ingestion & Processing**:
   - Upload multiple PDF/DOCX resumes simultaneously.
   - Extracts structured candidate metadata: Name, Contact Info (Email, Phone, Links), Skills, Experience, Projects, Education, and Certifications.
   - Chunks text while preserving page numbers, section headers, candidate IDs, and resume references.

2. **Semantic Vector Search (ChromaDB + SentenceTransformers)**:
   - Recruiter can enter natural-language search queries such as *"Candidates with Machine Learning experience"* or *"Python and SQL developers"*.
   - Uses `sentence-transformers/all-MiniLM-L6-v2` vector embeddings and ChromaDB cosine similarity search (no key required for search).
   - Groups retrieved vector chunks by candidate and ranks candidate cards by match percentage.

3. **Detailed Candidate Profile View**:
   - Dedicated Candidate Profile page displaying candidate overview, skills pills, work history, projects, education, certifications, and extracted resume text.

4. **Resume-Grounded Interview Question Generation**:
   - Generates personalized interview questions categorized into **Technical**, **Project-Based**, and **Behavioral** categories.
   - Each question includes an explicit **Grounded in Resume** quote box and evaluation guidelines for the recruiter.
   - Strictly grounded in facts present in the resume — zero hallucinations.

---

## 📁 Project Structure

```
ResumeRAG/
│
├── backend/
│   ├── main.py                     # FastAPI Application Entry Point
│   ├── api/
│   │   ├── upload.py               # Resume Upload & Candidate Listing APIs
│   │   ├── search.py               # Semantic Search API
│   │   ├── candidate.py            # Candidate Details API
│   │   └── interview.py            # Grounded Interview Question Generation API
│   ├── rag/
│   │   ├── loader.py               # PDF/DOCX parser & section/metadata extractor
│   │   ├── chunker.py              # Metadata-rich section text chunker
│   │   ├── embeddings.py           # SentenceTransformers vector embedding engine
│   │   ├── vector_store.py         # ChromaDB client & collection store
│   │   ├── retriever.py            # Semantic search retriever & candidate grouper
│   │   └── generator.py            # Grounded interview question generator (Gemini / Heuristic)
│   ├── services/
│   │   ├── resume_service.py       # Resume ingestion & candidate JSON storage service
│   │   ├── search_service.py       # Candidate search service
│   │   └── interview_service.py    # Interview question service
│   ├── data/
│   │   ├── resumes/                # Uploaded resume files
│   │   ├── chroma_db/              # Persistent ChromaDB vector database
│   │   └── profiles.json           # Candidate profile metadata store
│   ├── requirements.txt            # Python dependencies
│   └── .env                        # Environment variables
│
├── frontend/
│   ├── index.html                  # Dashboard & Multi-Resume Upload Page
│   ├── search.html                 # Recruiter Semantic Search Page
│   ├── candidate.html              # Candidate Details & Profile Page
│   ├── interview.html              # Interview Questions Page
│   ├── css/
│   │   ├── style.css               # Global glassmorphism design system & typography
│   │   ├── search.css              # Search bar, suggestion chips & candidate cards
│   │   └── interview.css           # Profile banner, question cards & grounding boxes
│   └── js/
│       ├── upload.js               # Upload page & dashboard stats handler
│       ├── search.js               # Semantic search query & card renderer
│       ├── candidate.js            # Profile details loader & tabbed renderer
│       └── interview.js            # Interview question fetcher & copy utility
│
└── README.md
```

---

## 🚀 How to Run

### 1. Configure Environment
Create or edit `.env` in the project root:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.0-flash
```
*(Note: An active `GEMINI_API_KEY` is required for online AI answer synthesis and candidate interview question generation).*

### 2. Start Backend Server (Python + FastAPI)
```bash
cd backend
.\.venv\Scripts\Activate.ps1   # On Windows (or source .venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
uvicorn main:app --reload
```
Backend server runs at `http://localhost:8000`.

### 3. Start Frontend Server (Vanilla HTML/CSS/JS)
In a second terminal window:
```bash
cd frontend
python -m http.server 5500
```
Open **`http://localhost:5500`** in your browser.

---

## 🧪 Running Tests

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_resumerag_system.py
```
