from job_market_ai_agent.qa.answer import (
    build_qa_prompt,
    format_search_detail_result,
    format_search_results,
    format_search_summary_results,
)
from job_market_ai_agent.qa.search import JobSearchResult


def _sample_result() -> JobSearchResult:
    return JobSearchResult(
        job={
            "title": "Backend Engineer",
            "company": {
                "name": "Example",
                "size_type": "\uc911\uc18c\uae30\uc5c5",
                "employee_count": "42 \uba85",
            },
            "location": {"summary": "\ub300\uc804 \uc720\uc131\uad6c", "address": "\ub300\uc804 \uc720\uc131\uad6c \ud14c\uc2a4\ud2b8\ub85c 1"},
            "job": {"category": "IT", "sub_categories": ["\ubc31\uc5d4\ub4dc/\uc11c\ubc84\uac1c\ubc1c", "\ub370\uc774\ud130\uc5d4\uc9c0\ub2c8\uc5b4"]},
            "employment": {"experience": "\uacbd\ub825 5\ub144 \uc774\uc0c1", "type": "\uc815\uaddc\uc9c1"},
            "dates": {
                "posted_at": "2026.07.01 00:00",
                "deadline": "2026.07.31 23:59",
                "deadline_text": "D-14",
            },
            "skills": ["Python", "AWS"],
            "analysis": {
                "required_skills": ["API"],
                "preferred_skills": ["LLM"],
                "main_tasks": ["\uc11c\ube44\uc2a4 \ubc31\uc5d4\ub4dc \uac1c\ubc1c"],
                "fit_for_8_9_year_developer": 0.8,
                "career_fit_reason": "\uacbd\ub825 \uac1c\ubc1c\uc790\uc5d0\uac8c \uc801\ud569\ud569\ub2c8\ub2e4.",
                "summary": "AI \uc11c\ube44\uc2a4 \uac1c\ubc1c \ud3ec\uc9c0\uc158\uc785\ub2c8\ub2e4.",
            },
            "url": "https://example.com/job",
        },
        score=5,
        matched_terms=["backend", "\ub300\uc804"],
    )


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

    prompt = build_qa_prompt("\ubc31\uc5d4\ub4dc \uacf5\uace0 \uc54c\ub824\uc918", [result])

    assert "\ubc31\uc5d4\ub4dc \uacf5\uace0 \uc54c\ub824\uc918" in prompt
    assert "Example" in prompt
    assert "https://example.com/job" in prompt
    assert "Do not mention majors" in prompt


def test_format_search_summary_results_outputs_top3_summary() -> None:
    output = format_search_summary_results([_sample_result()])

    assert "\uac80\uc0c9 \ud6c4\ubcf4 Top 3" in output
    assert "Example" in output
    assert "\ub300\uc804 \uc720\uc131\uad6c" in output
    assert "\uacbd\ub825 5\ub144 \uc774\uc0c1" in output
    assert "Python" in output
    assert "80%" in output
    assert "D-14" in output
    assert "https://example.com/job" in output
    assert "\uc8fc\uc18c:" not in output
    assert "detail" in output


def test_format_search_results_uses_summary_format() -> None:
    assert format_search_results([_sample_result()]) == format_search_summary_results([_sample_result()])


def test_format_search_detail_result_outputs_full_candidate() -> None:
    output = format_search_detail_result(_sample_result(), index=1)

    assert "1. Example" in output
    assert "\uc8fc\uc18c:" in output
    assert "\uc911\uc18c\uae30\uc5c5" in output
    assert "42 \uba85" in output
    assert "\uc11c\ube44\uc2a4 \ubc31\uc5d4\ub4dc \uac1c\ubc1c" in output
    assert "\uc801\ud569 \uc774\uc720" in output
    assert "AI \uc11c\ube44\uc2a4" in output


def test_format_search_results_handles_empty() -> None:
    assert format_search_results([]) == "\uac80\uc0c9\ub41c \uacf5\uace0\uac00 \uc5c6\uc2b5\ub2c8\ub2e4."
