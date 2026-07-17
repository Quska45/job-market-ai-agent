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


def test_format_search_results_outputs_candidates() -> None:
    result = JobSearchResult(
        job={
            "title": "Backend Engineer",
            "company": {"name": "Example"},
            "dates": {"deadline_text": "D-7"},
            "url": "https://example.com/job",
        },
        score=5,
        matched_terms=["backend"],
    )

    output = format_search_results([result])

    assert "검색 후보" in output
    assert "Example" in output
    assert "D-7" in output


def test_format_search_results_handles_empty() -> None:
    assert format_search_results([]) == "검색된 공고가 없습니다."

