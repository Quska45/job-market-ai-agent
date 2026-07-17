import pytest

from job_market_ai_agent.analysis.ollama_client import analyze_job_with_ollama


class DummyResponse:
    status_code = 200

    def json(self):
        return {
            "message": {
                "content": """
                {
                  "role_category": "AI Engineer",
                  "seniority": "Mid/Senior",
                  "required_skills": ["Python"],
                  "preferred_skills": ["RAG"],
                  "main_tasks": ["AI 시스템 개발"],
                  "domain": "AI/Software",
                  "fit_for_beginner": 0.2,
                  "fit_for_8_9_year_developer": 0.8,
                  "career_fit_reason": "Production AI development experience is relevant.",
                  "senior_keywords": ["production", "ownership"],
                  "summary": "AI 개발자 공고",
                  "evidence": ["Python 기반 개발"]
                }
                """
            }
        }


def test_analyze_job_with_ollama_parses_json_response(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        return DummyResponse()

    monkeypatch.setattr("job_market_ai_agent.analysis.ollama_client.httpx.post", fake_post)

    analysis = analyze_job_with_ollama({"title": "AI Engineer"}, model="test-model")

    assert analysis.role_category == "AI Engineer"
    assert analysis.required_skills == ["Python"]
    assert analysis.fit_for_8_9_year_developer == 0.8
