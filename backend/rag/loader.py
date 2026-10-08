"""Extract text and metadata from PDF/DOCX resumes."""
import re
from pathlib import Path
from typing import Dict, List, Any


def extract_contact_info(text: str) -> Dict[str, str]:
    """Extract email, phone, and links using regex."""
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    phone_match = re.search(r"(\+?\d{1,3}[\s\-])?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}", text)
    linkedin_match = re.search(r"(linkedin\.com/in/[a-zA-Z0-9_-]+)", text, re.IGNORECASE)
    github_match = re.search(r"(github\.com/[a-zA-Z0-9_-]+)", text, re.IGNORECASE)

    return {
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0) if phone_match else "",
        "linkedin": linkedin_match.group(0) if linkedin_match else "",
        "github": github_match.group(0) if github_match else "",
    }


COMMON_SKILLS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "html", "css", "sql", "nosql",
    "machine learning", "deep learning", "nlp", "natural language processing", "generative ai",
    "rag", "chromadb", "faiss", "langchain", "tensorflow", "pytorch", "scikit-learn", "pandas",
    "numpy", "predictive modeling", "random forest", "xgboost", "data analysis", "docker",
    "kubernetes", "aws", "gcp", "azure", "fastapi", "flask", "django", "react", "node.js",
    "git", "ci/cd", "rest api", "graphql", "spark", "hadoop", "tableau", "power bi"
]


def extract_skills(text: str) -> List[str]:
    """Find skill keywords present in the text."""
    text_lower = text.lower()
    found = []
    for skill in COMMON_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill.title() if len(skill) <= 4 else skill.capitalize())
    return list(dict.fromkeys(found))


SECTION_ALIASES = {
    "summary": ["summary", "profile", "objective", "career objective", "about me", "professional summary"],
    "education": ["education", "academic background", "academics", "qualifications", "education history"],
    "skills": ["skills", "technical skills", "core competencies", "technologies", "tech stack", "skills & tools"],
    "projects": ["projects", "academic projects", "personal projects", "key projects", "key technical projects"],
    "experience": ["experience", "work experience", "professional experience", "employment history", "internships", "work history"],
    "certifications": ["certifications", "certificates", "awards", "honors", "accomplishments", "achievements", "licenses"],
}

_LOOKUP = {alias: name for name, aliases in SECTION_ALIASES.items() for alias in aliases}


def detect_heading(line: str) -> str | None:
    text = re.sub(r"^[#\s]+", "", line.strip().lower())
    text = re.sub(r"[:\-–—_\s]+$", "", text)
    if 0 < len(text) <= 40:
        return _LOOKUP.get(text)
    return None


def parse_resume_file(path: Path) -> Dict[str, Any]:
    """
    Parse PDF or DOCX file into structured pages, sections, and metadata.
    Returns dict with pages, raw_text, sections, name, contact, skills, etc.
    """
    ext = path.suffix.lower()
    if ext == ".pdf":
        pages = _parse_pdf(path)
    elif ext == ".docx":
        pages = _parse_docx(path)
    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX.")

    full_text = "\n\n".join(p["text"] for p in pages)
    if not full_text.strip():
        raise ValueError("No readable text found in document.")

    sections = split_into_sections(pages)
    candidate_name = extract_candidate_name(sections, path.name)
    contact_info = extract_contact_info(full_text)
    skills = extract_skills(full_text)

    # Group text by main section types
    section_dict = {
        "summary": "",
        "education": "",
        "skills": "",
        "experience": "",
        "projects": "",
        "certifications": ""
    }
    for sec in sections:
        stype = sec["section"]
        if stype in section_dict:
            section_dict[stype] = (section_dict[stype] + "\n" + sec["text"]).strip()

    return {
        "candidate_name": candidate_name,
        "contact_info": contact_info,
        "skills": skills,
        "sections": sections,
        "section_dict": section_dict,
        "full_text": full_text,
        "pages": pages
    }


def _parse_pdf(path: Path) -> List[Dict[str, Any]]:
    import fitz  # PyMuPDF

    try:
        with fitz.open(path) as doc:
            if doc.is_encrypted:
                raise ValueError("Password-protected PDF files are not supported.")
            return [{"page": i + 1, "text": page.get_text()} for i, page in enumerate(doc)]
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Failed to parse PDF file: {exc}")


def _parse_docx(path: Path) -> List[Dict[str, Any]]:
    from docx import Document

    try:
        doc = Document(str(path))
        lines = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                lines.append(" | ".join(cell.text.strip() for cell in row.cells if cell.text.strip()))
        return [{"page": 1, "text": "\n".join(lines)}]
    except Exception as exc:
        raise ValueError(f"Failed to parse DOCX file: {exc}")


def split_into_sections(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []
    current, start_page, buffer = "header", 1, []

    def flush():
        text = "\n".join(buffer).strip()
        if text:
            sections.append({"section": current, "page": start_page, "text": text})
        buffer.clear()

    for page in pages:
        for line in page["text"].split("\n"):
            heading = detect_heading(line)
            if heading:
                flush()
                current = heading
                continue
            if not buffer and not line.strip():
                continue
            if not buffer:
                start_page = page["page"]
            buffer.append(line)
    flush()
    return sections


def extract_candidate_name(sections: List[Dict[str, Any]], filename: str) -> str:
    """Extract name from header section or fall back to filename."""
    for s in sections:
        if s.get("section") == "header" and s.get("text"):
            for line in s["text"].split("\n"):
                cleaned = line.strip()
                cleaned = re.sub(r"^[•\-*#\s]+", "", cleaned).strip()
                if cleaned and len(cleaned) <= 60:
                    if cleaned.lower() in ["resume", "curriculum vitae", "cv", "profile", "summary"]:
                        continue
                    name_part = re.split(r"[|•,;]", cleaned)[0].strip()
                    if name_part and len(name_part) >= 2:
                        return name_part
    base = Path(filename).stem
    clean_base = re.sub(r"[_\-]+", " ", base).title().strip()
    return clean_base or filename
