from job_market_ai_agent.reporting.export import (
    REPORT_COLUMNS,
    build_report_rows,
    classify_deadline,
    export_csv,
    export_markdown,
)


def test_build_report_rows_includes_experienced_fit_and_dates() -> None:
    rows = build_report_rows(
        [
            {
                "title": "Senior Backend Engineer",
                "url": "https://example.com/job",
                "company": {"name": "Example"},
                "location": {"summary": "Daejeon", "address": "Daejeon Seo-gu"},
                "employment": {"experience": "8 years+"},
                "dates": {
                    "posted_at": "2026.07.17 09:00",
                    "deadline": "2026.08.01 23:59",
                    "deadline_text": "D-15",
                },
                "analysis": {
                    "role_category": "Backend Developer",
                    "seniority": "Senior",
                    "required_skills": ["Python", "SQL"],
                    "preferred_skills": ["AWS"],
                    "fit_for_8_9_year_developer": 0.82,
                    "career_fit_reason": "Requires senior backend ownership.",
                },
            }
        ]
    )

    assert rows[0]["company"] == "Example"
    assert rows[0]["fit_for_8_9_year_developer"] == "0.82"
    assert rows[0]["posted_at"] == "2026.07.17 09:00"
    assert rows[0]["deadline_type"] == "fixed_deadline"
    assert rows[0]["required_skills"] == "Python, SQL"


def test_classify_deadline_detects_until_hired() -> None:
    assert classify_deadline({"deadline_text": "채용시 마감"}) == "until_hired"
    assert classify_deadline({"deadline_text": "상시채용"}) == "always_open"
    assert classify_deadline({"deadline_text": "D-3"}) == "fixed_deadline"


def test_export_csv_and_markdown() -> None:
    row = {column: "" for column in REPORT_COLUMNS}
    row["company"] = "Example"
    row["title"] = "Backend | AI"

    csv_content = export_csv([row])
    markdown_content = export_markdown([row])

    assert "company,title" in csv_content
    assert "Example" in csv_content
    assert "Backend \\| AI" in markdown_content
