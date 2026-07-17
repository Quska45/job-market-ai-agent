from datetime import datetime

from apps.pipeline.daily_job_pipeline import _expected_output_path


def test_expected_output_path_uses_today_and_keyword(monkeypatch) -> None:
    path = _expected_output_path("AI Engineer")

    today = datetime.now().astimezone().strftime("%Y-%m-%d")
    assert str(path).replace("\\", "/") == f"data/raw/saramin/{today}_AI_Engineer.json"
