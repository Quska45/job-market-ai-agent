from job_market_ai_agent.analysis.prompts import SYSTEM_PROMPT, build_job_analysis_prompt


def test_build_job_analysis_prompt_includes_schema_and_job_content() -> None:
    prompt = build_job_analysis_prompt(
        {
            "title": "AI Engineer",
            "company": {"name": "Example"},
            "location": {"summary": "Daejeon"},
            "job": {"sub_categories": ["AI/ML"]},
            "employment": {"experience": "8 years+"},
            "dates": {"posted_at": "2026.07.17", "deadline_text": "D-7"},
            "content": {
                "description": "Build Python based LLM/RAG systems",
                "sections": {"requirements": "Python", "preferences": "RAG"},
                "image_urls": ["https://example.com/a.png"],
            },
        }
    )

    assert "JobAnalysis" in prompt
    assert "role_category" in prompt
    assert "fit_for_8_9_year_developer" in prompt
    assert "8-9 years" in prompt
    assert "Build Python based LLM/RAG systems" in prompt
    assert "AI Engineer" in prompt


def test_build_job_analysis_prompt_can_limit_local_content_size() -> None:
    prompt = build_job_analysis_prompt(
        {
            "title": "AI Engineer",
            "content": {
                "description": "A" * 200,
                "sections": {"requirements": "B" * 200},
                "image_urls": [],
            },
        },
        max_content_chars=50,
    )

    assert "TRUNCATED_FOR_LOCAL_ANALYSIS" in prompt
    assert "A" * 100 not in prompt


def test_system_prompt_requires_json_only_and_targets_experienced_developer() -> None:
    assert "Return only valid JSON" in SYSTEM_PROMPT
    assert "8-9 years" in SYSTEM_PROMPT
