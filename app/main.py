import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field


load_dotenv()

app = FastAPI(title="AI Resume Optimizer")
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
COMMON_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "looking",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "this",
    "to",
    "we",
    "with",
    "you",
    "your",
    "experience",
}

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ResumeRequest(BaseModel):
    resume_text: str = Field(..., min_length=1)
    job_description: str = Field(..., min_length=1)


class OptimizeResumeResponse(BaseModel):
    match_score: int
    professional_summary: str
    improved_bullets: list[str]
    missing_keywords: list[str]
    ats_recommendations: list[str]


def extract_keywords(text: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    words = normalized.split()
    return {word for word in words if word not in COMMON_WORDS}


def calculate_match_score(resume_text: str, job_description: str) -> int:
    keywords = extract_keywords(job_description)
    if not keywords:
        return 0

    resume_words = extract_keywords(resume_text)
    matched_keywords = keywords.intersection(resume_words)
    return round((len(matched_keywords) / len(keywords)) * 100)


@app.get("/")
def homepage() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/optimize-resume", response_model=OptimizeResumeResponse)
def optimize_resume(data: ResumeRequest) -> OptimizeResumeResponse:
    match_score = calculate_match_score(
        data.resume_text,
        data.job_description,
    )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        completion = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert resume optimizer. Return only valid JSON with "
                        "these keys: professional_summary, improved_bullets, "
                        "missing_keywords, ats_recommendations."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Optimize this resume for the job description.\n\n"
                        f"Resume:\n{data.resume_text}\n\n"
                        f"Job Description:\n{data.job_description}\n\n"
                        "Return JSON in this exact shape:\n"
                        "{\n"
                        '  "professional_summary": "string",\n'
                        '  "improved_bullets": ["string"],\n'
                        '  "missing_keywords": ["string"],\n'
                        '  "ats_recommendations": ["string"]\n'
                        "}"
                    ),
                },
            ],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI request failed: {exc}") from exc

    content = completion.choices[0].message.content
    if not content:
        raise HTTPException(status_code=502, detail="OpenAI returned an empty response.")

    try:
        data = json.loads(content)
        data["match_score"] = match_score
        return OptimizeResumeResponse(**data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="OpenAI returned an invalid response.") from exc
