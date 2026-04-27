import json
import os
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

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class OptimizeResumeRequest(BaseModel):
    resume_text: str = Field(..., min_length=1)
    job_description: str = Field(..., min_length=1)


class OptimizeResumeResponse(BaseModel):
    professional_summary: str
    improved_bullets: list[str]
    missing_keywords: list[str]
    ats_recommendations: list[str]


@app.get("/")
def homepage() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/optimize-resume", response_model=OptimizeResumeResponse)
def optimize_resume(payload: OptimizeResumeRequest) -> OptimizeResumeResponse:
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
                        f"Resume:\n{payload.resume_text}\n\n"
                        f"Job Description:\n{payload.job_description}\n\n"
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
        return OptimizeResumeResponse(**data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="OpenAI returned an invalid response.") from exc
