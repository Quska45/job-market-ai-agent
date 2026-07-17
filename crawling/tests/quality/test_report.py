from job_market_ai_agent.quality.report import build_quality_report, format_quality_report


def test_build_quality_report_counts_missing_fields_and_description_lengths() -> None:
    rows = [
        {
            "source": "saramin",
            "source_job_id": "1",
            "url": "https://example.com/1",
            "title": "AI Engineer",
            "company": {"name": "Example"},
            "location": {"summary": "대전"},
            "job": {"sub_categories": ["AI"]},
            "employment": {"experience": "신입"},
            "dates": {"deadline_text": "D-7"},
            "content": {"description": "a" * 100, "image_urls": ["https://example.com/a.png"]},
            "crawl": {"content_hash": "hash"},
        },
        {
            "source": "saramin",
            "source_job_id": "2",
            "url": "https://example.com/2",
            "title": "Backend Developer",
            "company": {"name": ""},
            "location": {"summary": None},
            "job": {"sub_categories": []},
            "employment": {"experience": "경력"},
            "dates": {"deadline_text": "채용시"},
            "content": {"description": "b" * 50, "image_urls": []},
            "crawl": {"content_hash": "hash2"},
        },
    ]

    report = build_quality_report(rows)

    assert report.total_jobs == 2
    assert report.missing_counts["company.name"] == 1
    assert report.missing_counts["job.sub_categories"] == 1
    assert report.description_min_length == 50
    assert report.description_max_length == 100
    assert report.jobs_with_images == 1


def test_format_quality_report_includes_key_sections() -> None:
    report = build_quality_report([])

    output = format_quality_report(report)

    assert "Job Data Quality Report" in output
    assert "field_fill_rates:" in output

