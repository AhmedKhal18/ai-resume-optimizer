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


def test_optimize_resume_uses_mocked_openai(monkeypatch):
    expected = {
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
