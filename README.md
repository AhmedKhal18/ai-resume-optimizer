# AI Resume Optimizer

A simple FastAPI backend that optimizes resume text against a job description using the OpenAI API.

## Project Structure

```text
app/
  main.py
  static/
    index.html
    script.js
    styles.css
requirements.txt
.env.example
README.md
```

## Setup

1. Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file:

```powershell
Copy-Item .env.example .env
```

4. Add your OpenAI API key to `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

## Run Locally

```powershell
uvicorn app.main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

## Use the Web UI

Open the homepage in your browser:

```text
http://127.0.0.1:8000
```

Paste your resume text or upload a PDF resume, add the target job description, then click **Optimize Resume**. The page will call `POST /api/optimize-resume` and display the professional summary, improved bullets, missing keywords, and ATS recommendations.

PDF uploads must be valid `.pdf` files and 5 MB or smaller. If text cannot be extracted from the PDF, paste the resume text into the form instead.

Interactive API docs are available at:

```text
http://127.0.0.1:8000/docs
```

## Run Tests

```powershell
pytest
```

## Endpoint

### POST `/api/optimize-resume`

JSON request body:

```json
{
  "resume_text": "Paste resume text here...",
  "job_description": "Paste job description here..."
}
```

Response body:

```json
{
  "match_score": 72,
  "professional_summary": "Updated professional summary...",
  "improved_bullets": ["Improved bullet 1", "Improved bullet 2"],
  "missing_keywords": ["keyword 1", "keyword 2"],
  "ats_recommendations": ["Recommendation 1", "Recommendation 2"]
}
```

The web UI sends `multipart/form-data` so it can include an optional `resume_pdf` file along with `resume_text` and `job_description`.
