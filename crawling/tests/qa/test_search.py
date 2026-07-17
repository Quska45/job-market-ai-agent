from job_market_ai_agent.qa.search import search_jobs, summarize_job_for_qa


def test_search_jobs_scores_structured_fields() -> None:
    jobs = [
        {
            "source_job_id": "1",
            "title": "Backend Python Engineer",
            "company": {"name": "A"},
            "location": {"summary": "Daejeon"},
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
            "location": {"summary": "Seoul"},
            "analysis": {"role_category": "Sales", "fit_for_8_9_year_developer": 0.1},
        },
    ]

    results = search_jobs("Daejeon Python Backend", jobs)

    assert [result.job["source_job_id"] for result in results] == ["1"]
    assert "python" in results[0].matched_terms


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
