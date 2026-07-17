from job_market_ai_agent.qa.answer import build_qa_prompt, format_search_results
from job_market_ai_agent.qa.search import JobSearchResult


def test_build_qa_prompt_includes_question_and_evidence() -> None:
    result = JobSearchResult(
        job={
            "source_job_id": "1",
            "title": "Backend Engineer",
            "company": {"name": "Example"},
            "url": "https://example.com/job",
        },
        score=5,
        matched_terms=["backend"],
    )

    prompt = build_qa_prompt("백엔드 공고 알려줘", [result])

    assert "백엔드 공고 알려줘" in prompt
    assert "Example" in prompt
    assert "https://example.com/job" in prompt
    assert "Do not mention majors" in prompt


def test_format_search_results_outputs_rich_candidates() -> None:
    result = JobSearchResult(
        job={
            "title": "Backend Engineer",
            "company": {
                "name": "Example",
                "size_type": "중소기업",
                "employee_count": "42 명",
            },
            "location": {"summary": "대전 유성구", "address": "대전 유성구 테스트로 1"},
            "job": {"category": "IT", "sub_categories": ["백엔드/서버개발", "데이터엔지니어"]},
            "employment": {"experience": "경력 5년 이상", "type": "정규직"},
            "dates": {
                "posted_at": "2026.07.01 00:00",
                "deadline": "2026.07.31 23:59",
                "deadline_text": "D-14",
            },
            "skills": ["Python", "AWS"],
            "analysis": {
                "required_skills": ["API"],
                "preferred_skills": ["LLM"],
                "main_tasks": ["서비스 백엔드 개발"],
                "fit_for_8_9_year_developer": 0.8,
                "career_fit_reason": "경력 개발자에게 적합합니다.",
                "summary": "AI 서비스 개발 포지션입니다.",
            },
            "url": "https://example.com/job",
        },
        score=5,
        matched_terms=["backend", "대전"],
    )

    output = format_search_results([result])

    assert "검색 후보" in output
    assert "Example" in output
    assert "대전 유성구" in output
    assert "중소기업" in output
    assert "42 명" in output
    assert "Python" in output
    assert "80%" in output
    assert "D-14" in output
    assert "https://example.com/job" in output


def test_format_search_results_handles_empty() -> None:
    assert format_search_results([]) == "검색된 공고가 없습니다."
