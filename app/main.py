import json
import os
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from pypdf import PdfReader


load_dotenv()

app = FastAPI(title="AI Resume Optimizer")
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
MAX_PDF_SIZE_BYTES = 5 * 1024 * 1024

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class OptimizeResumeRequest(BaseModel):
    resume_text: str = Field(..., min_length=1)
    job_description: str = Field(..., min_length=1)


class OptimizeResumeResponse(BaseModel):
    professional_summary: str
    improved_bullets: list[str]
    missing_keywords: list[str]
    ats_recommendations: list[str]


async def extract_pdf_text(file: UploadFile) -> str:
    filename = (file.filename or "").lower()
    content_type = file.content_type or ""

    if not filename.endswith(".pdf") or content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Please upload a valid PDF file.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="PDF file must be 5 MB or smaller.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the PDF. Please try a text-based PDF or paste the resume text.",
        ) from exc

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the PDF. Please try a text-based PDF or paste the resume text.",
        )

    return text


async def parse_optimize_request(request: Request) -> OptimizeResumeRequest:
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        form = await request.form()
        resume_text = str(form.get("resume_text") or "").strip()
        job_description = str(form.get("job_description") or "").strip()
        resume_pdf = form.get("resume_pdf")

        if resume_pdf and getattr(resume_pdf, "filename", ""):
            resume_text = await extract_pdf_text(resume_pdf)

        try:
            return OptimizeResumeRequest(
                resume_text=resume_text,
                job_description=job_description,
            )
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc

    try:
        return OptimizeResumeRequest.model_validate(await request.json())
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


@app.get("/")
def homepage() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/optimize-resume", response_model=OptimizeResumeResponse)
async def optimize_resume(request: Request) -> OptimizeResumeResponse:
    payload = await parse_optimize_request(request)

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
