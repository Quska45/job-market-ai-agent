from job_market_ai_agent.reporting.summary import build_notification_summary


def test_build_notification_summary_orders_by_experienced_fit() -> None:
    summary = build_notification_summary(
        [
            {
                "title": "Low",
                "company": {"name": "A"},
                "dates": {"deadline_text": "D-3"},
                "analysis": {"fit_for_8_9_year_developer": 0.2},
            },
            {
                "title": "High",
                "company": {"name": "B"},
                "dates": {"deadline_text": "채용시 마감"},
                "analysis": {"fit_for_8_9_year_developer": 0.9},
            },
        ]
    )

    assert "collected_jobs: 2" in summary
    assert "analyzed_jobs: 2" in summary
    assert summary.index("B | High") < summary.index("A | Low")
