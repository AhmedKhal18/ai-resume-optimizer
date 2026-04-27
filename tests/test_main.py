import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


def test_homepage_returns_200():
    response = client.get("/")

    assert response.status_code == 200


def test_optimize_resume_rejects_empty_resume_text():
    response = client.post(
        "/api/optimize-resume",
        json={
            "resume_text": "",
            "job_description": "We need a Python developer.",
        },
    )

    assert response.status_code == 422


def test_optimize_resume_rejects_empty_job_description():
    response = client.post(
        "/api/optimize-resume",
        json={
            "resume_text": "Experienced Python developer.",
            "job_description": "",
        },
    )

    assert response.status_code == 422


def test_optimize_resume_rejects_non_pdf_upload():
    response = client.post(
        "/api/optimize-resume",
        data={"job_description": "We need a Python developer."},
        files={"resume_pdf": ("resume.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Please upload a valid PDF file."


def test_optimize_resume_rejects_large_pdf_upload():
    response = client.post(
        "/api/optimize-resume",
        data={"job_description": "We need a Python developer."},
        files={
            "resume_pdf": (
                "resume.pdf",
                b"0" * (main.MAX_PDF_SIZE_BYTES + 1),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "PDF file must be 5 MB or smaller."


def test_match_score_is_high_for_identical_keywords():
    score = main.calculate_match_score(
        "Python FastAPI AWS Docker APIs PostgreSQL",
        "Looking for Python FastAPI AWS Docker APIs PostgreSQL experience",
    )

    assert score == 100


def test_match_score_is_low_for_unrelated_keywords():
    score = main.calculate_match_score(
        "Graphic design branding typography",
        "Python FastAPI AWS Docker PostgreSQL",
    )

    assert score == 0


def test_match_score_is_medium_for_partial_overlap():
    score = main.calculate_match_score(
        "Python FastAPI communication leadership",
        "Python FastAPI AWS Docker",
    )

    assert score == 50


def test_optimize_resume_uses_mocked_openai(monkeypatch):
    expected = {
        "match_score": 50,
        "professional_summary": "Python developer with API experience.",
        "improved_bullets": ["Built FastAPI services."],
        "missing_keywords": ["CI/CD"],
        "ats_recommendations": ["Add measurable impact."],
    }

    class MockCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=json.dumps(expected))
                    )
                ]
            )

    class MockOpenAI:
        def __init__(self, api_key):
            self.chat = SimpleNamespace(
                completions=MockCompletions()
            )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(main, "OpenAI", MockOpenAI)

    response = client.post(
        "/api/optimize-resume",
        json={
            "resume_text": "Experienced Python developer.",
            "job_description": "We need a Python developer with FastAPI experience.",
        },
    )

    assert response.status_code == 200
    assert response.json() == expected
