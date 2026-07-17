from pathlib import Path

from job_market_ai_agent.qa.service import answer_job_question


def test_answer_job_question_returns_candidates_without_llm(tmp_path) -> None:
    data_path = tmp_path / "jobs.json"
    data_path.write_text(
        """
        {
          "jobs": [
            {
              "source_job_id": "1",
              "title": "AI Engineer",
              "company": {"name": "Example"},
              "location": {"summary": "대전"},
              "dates": {"deadline_text": "D-7"},
              "analysis": {"role_category": "AI Engineer", "fit_for_8_9_year_developer": 0.9},
              "url": "https://example.com/job"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    output = answer_job_question("대전 AI", input_path=data_path, no_llm=True)

    assert "검색 후보" in output
    assert "Example" in output
