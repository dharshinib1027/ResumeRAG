"""Generate grounded interview questions and search answers using Gemini LLM."""
import json
import os
from typing import Dict, List, Any

LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")


def get_gemini_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is missing. An active Gemini API key is required."
        )
    return key


def generate_search_answer(query: str, candidate_matches: List[Dict[str, Any]]) -> str:
    """
    Synthesize a direct, concise AI answer to the recruiter's exact search question using Gemini API.
    """
    if not candidate_matches:
        return "No relevant candidate resumes found matching your query."

    api_key = get_gemini_api_key()

    # Build context from top matching candidate excerpts
    context_blocks = []
    for cand in candidate_matches[:3]:
        name = cand.get("candidate_name", "Candidate")
        excerpts = "\n".join(cand.get("top_excerpts", [])[:2])
        context_blocks.append(f"Candidate: {name}\nExcerpts:\n{excerpts}")

    context_str = "\n\n".join(context_blocks)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = f"""You are an AI recruitment assistant. Answer the recruiter's exact search query directly and concisely in 2 to 4 sentences based ONLY on the provided resume context.
Name the top matching candidate(s) and highlight their exact skills or project experience.

Recruiter Search Query: "{query}"

Retrieved Resume Context:
-------------------
{context_str[:3000]}
-------------------
"""
        resp = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="Be direct, factual, professional, and clear. Do not hallucinate.",
                max_output_tokens=300,
                temperature=0.2,
            )
        )
        if resp.text:
            return resp.text.strip()
        raise RuntimeError("Gemini API returned an empty text response for search answer.")
    except Exception as exc:
        raise RuntimeError(f"Gemini API generation failed: {exc}")


def generate_interview_questions(
    candidate_name: str,
    candidate_profile: Dict[str, Any],
    resume_context: str
) -> Dict[str, Any]:
    """
    Generate interview questions strictly grounded in the candidate's resume context using Gemini API.
    Returns dict with keys: candidate_name, generated_via, questions.
    """
    api_key = get_gemini_api_key()

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = f"""You are a senior technical recruiter generating interview questions for candidate '{candidate_name}'.
You MUST strictly base all questions on the provided resume context. DO NOT invent or assume any skills, projects, companies, or qualifications not explicitly listed.

Candidate Resume Context:
-------------------
{resume_context[:3500]}
-------------------

Generate 6 to 9 personalized, grounded interview questions divided into 3 categories:
1. Technical Questions (evaluating candidate's specific technologies/tools listed)
2. Project-Based Questions (evaluating specific projects/implementations listed)
3. Behavioral & Experience Questions (evaluating work history/roles listed)

Respond with JSON ONLY using this exact JSON structure:
{{
  "technical": [
    {{
      "question": "Question text here?",
      "difficulty": "Easy" | "Medium" | "Hard",
      "grounding_context": "Exact skill or line from resume that inspired this question",
      "what_to_look_for": "Key technical concepts to check in candidate answer"
    }}
  ],
  "project_based": [
    {{
      "question": "Question text here?",
      "difficulty": "Medium" | "Hard",
      "grounding_context": "Exact project title/description from resume",
      "what_to_look_for": "Key architecture, design, and problem solving details"
    }}
  ],
  "behavioral": [
    {{
      "question": "Question text here?",
      "difficulty": "Easy" | "Medium",
      "grounding_context": "Exact role/company/experience from resume",
      "what_to_look_for": "Leadership, communication, and process handling skills"
    }}
  ]
}}
"""
        resp = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are an expert HR recruitment interviewer. Always respond with valid JSON only.",
                temperature=0.2,
                max_output_tokens=1500,
            )
        )

        raw_text = resp.text if resp.text else ""
        if raw_text:
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start != -1 and end != -1:
                json_data = json.loads(raw_text[start:end])
                return {
                    "candidate_name": candidate_name,
                    "generated_via": "Gemini 2.0 AI",
                    "questions": json_data
                }
        raise RuntimeError("Gemini API returned an empty or invalid JSON response.")
    except Exception as exc:
        raise RuntimeError(f"Gemini API question generation failed: {exc}")

