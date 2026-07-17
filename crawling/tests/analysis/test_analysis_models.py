import pytest
from pydantic import ValidationError

from job_market_ai_agent.analysis.models import JobAnalysis


def test_job_analysis_accepts_expected_fields() -> None:
    analysis = JobAnalysis(
        role_category="AI Engineer",
        seniority="Mid/Senior",
        required_skills=["Python", "RAG"],
        preferred_skills=["Docker"],
        main_tasks=["Build LLM/RAG systems"],
        domain="AI/Software",
        fit_for_beginner=0.2,
        fit_for_8_9_year_developer=0.85,
        career_fit_reason="Requires ownership and production AI delivery experience.",
        senior_keywords=["ownership", "architecture"],
        summary="Experienced AI engineering role",
        evidence=["Python based development"],
    )

    assert analysis.role_category == "AI Engineer"
    assert analysis.fit_for_beginner == 0.2
    assert analysis.fit_for_8_9_year_developer == 0.85


def test_job_analysis_rejects_invalid_experienced_score() -> None:
    with pytest.raises(ValidationError):
        JobAnalysis(
            role_category="AI Engineer",
            seniority="Senior",
            fit_for_8_9_year_developer=1.5,
            summary="invalid score",
        )
