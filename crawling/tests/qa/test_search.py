from job_market_ai_agent.qa.search import search_jobs, summarize_job_for_qa


def test_search_jobs_scores_structured_fields() -> None:
    jobs = [
        {
            "source_job_id": "1",
            "title": "Backend Python Engineer",
            "company": {"name": "A"},
            "location": {"summary": "대전"},
            "dates": {"deadline_text": "D-7"},
            "analysis": {
                "role_category": "Backend Developer",
                "required_skills": ["Python"],
                "fit_for_8_9_year_developer": 0.9,
            },
        },
        {
            "source_job_id": "2",
            "title": "Sales Manager",
            "company": {"name": "B"},
            "location": {"summary": "서울"},
            "dates": {"deadline_text": "D-7"},
            "analysis": {"role_category": "Sales", "fit_for_8_9_year_developer": 0.1},
        },
    ]

    results = search_jobs("대전 Python Backend", jobs)

    assert [result.job["source_job_id"] for result in results] == ["1"]
    assert "python" in results[0].matched_terms


def test_search_jobs_filters_by_region_and_deadline_type() -> None:
    jobs = [
        {
            "source_job_id": "1",
            "title": "AI Engineer",
            "location": {"summary": "대전"},
            "dates": {"deadline_text": "채용시 마감"},
            "analysis": {"role_category": "AI Engineer", "fit_for_8_9_year_developer": 0.8},
        },
        {
            "source_job_id": "2",
            "title": "AI Engineer",
            "location": {"summary": "세종"},
            "dates": {"deadline_text": "D-7"},
            "analysis": {"role_category": "AI Engineer", "fit_for_8_9_year_developer": 0.9},
        },
    ]

    results = search_jobs("대전 채용시 AI 공고", jobs)

    assert [result.job["source_job_id"] for result in results] == ["1"]


def test_search_jobs_prioritizes_experienced_fit() -> None:
    jobs = [
        {
            "source_job_id": "1",
            "title": "AI Engineer",
            "location": {"summary": "대전"},
            "analysis": {"role_category": "AI Engineer", "fit_for_8_9_year_developer": 0.3},
        },
        {
            "source_job_id": "2",
            "title": "AI Engineer",
            "location": {"summary": "대전"},
            "analysis": {"role_category": "AI Engineer", "fit_for_8_9_year_developer": 1.0},
        },
    ]

    results = search_jobs("대전 8-9년차 AI 공고", jobs)

    assert [result.job["source_job_id"] for result in results] == ["2", "1"]


def test_summarize_job_for_qa_truncates_description() -> None:
    summary = summarize_job_for_qa(
        {
            "source_job_id": "1",
            "title": "AI Engineer",
            "company": {"name": "A"},
            "content": {"description": "A" * 1200},
            "analysis": {"required_skills": ["Python"]},
        }
    )

    assert summary["company"] == "A"
    assert summary["analysis"]["required_skills"] == ["Python"]
    assert summary["description_excerpt"].endswith("...")
