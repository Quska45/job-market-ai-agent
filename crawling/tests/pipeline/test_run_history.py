import json
import subprocess

import pytest

from job_market_ai_agent.pipeline.run_history import (
    PipelineRunHistory,
    build_failure_summary,
    format_run_detail,
    format_run_list,
    list_run_records,
    load_run_record,
)


def test_pipeline_run_history_records_success_step(tmp_path) -> None:
    history = PipelineRunHistory.create(tmp_path, run_id="test-run")

    with history.step("collect"):
        history.collected_jobs = 3

    history.mark_success()
    payload = json.loads((tmp_path / "test-run" / "run.json").read_text(encoding="utf-8"))

    assert payload["status"] == "success"
    assert payload["collected_jobs"] == 3
    assert payload["steps"][0]["name"] == "collect"
    assert payload["steps"][0]["status"] == "success"


def test_pipeline_run_history_records_failure_step(tmp_path) -> None:
    history = PipelineRunHistory.create(tmp_path, run_id="failed-run")

    with pytest.raises(ValueError):
        with history.step("analyze"):
            raise ValueError("model timeout")

    payload = json.loads((tmp_path / "failed-run" / "run.json").read_text(encoding="utf-8"))

    assert payload["status"] == "failed"
    assert payload["failed_step"] == "analyze"
    assert payload["steps"][0]["status"] == "failed"
    assert (tmp_path / "failed-run" / "error.txt").exists()


def test_pipeline_run_history_records_subprocess_output_on_failure(tmp_path) -> None:
    history = PipelineRunHistory.create(tmp_path, run_id="subprocess-failed")
    error = subprocess.CalledProcessError(
        returncode=1,
        cmd=["demo"],
        output="stdout text",
        stderr="stderr text",
    )

    history.mark_failed("collect", error)
    error_text = (tmp_path / "subprocess-failed" / "error.txt").read_text(encoding="utf-8")

    assert "stdout text" in error_text
    assert "stderr text" in error_text


def test_list_and_load_run_records(tmp_path) -> None:
    first = PipelineRunHistory.create(tmp_path, run_id="2026-07-17_090000")
    first.mark_success()
    second = PipelineRunHistory.create(tmp_path, run_id="2026-07-18_090000")
    second.mark_success()

    records = list_run_records(tmp_path, limit=1)
    loaded = load_run_record("2026-07-18_090000", tmp_path)

    assert [record["run_id"] for record in records] == ["2026-07-18_090000"]
    assert loaded["status"] == "success"


def test_format_run_list_and_detail() -> None:
    record = {
        "run_id": "2026-07-18_090000",
        "status": "failed",
        "failed_step": "analyze",
        "started_at": "2026-07-18T09:00:00+09:00",
        "finished_at": "2026-07-18T09:10:00+09:00",
        "error_message": "timeout",
        "output_json": "data/raw/saramin/2026-07-18_AI.json",
        "report_path": None,
        "collected_jobs": 10,
        "analyzed_jobs": 4,
        "notified_channels": ["discord"],
        "steps": [
            {"name": "collect", "status": "success", "duration_seconds": 3.2},
            {"name": "analyze", "status": "failed", "duration_seconds": 600, "error_message": "timeout"},
        ],
    }

    list_text = format_run_list([record])
    detail_text = format_run_detail(record)

    assert "2026-07-18_090000" in list_text
    assert "failed" in list_text
    assert "failed_step: analyze" in detail_text
    assert "- analyze: failed (600s)" in detail_text


def test_format_run_list_handles_empty_records() -> None:
    assert format_run_list([]) == "No run history found."


def test_build_failure_summary_includes_history_path(tmp_path) -> None:
    history = PipelineRunHistory.create(tmp_path, run_id="failed-run")
    try:
        raise RuntimeError("boom")
    except RuntimeError as error:
        history.mark_failed("report", error)

    summary = build_failure_summary(history)

    assert "채용공고 파이프라인 실패" in summary
    assert "failed_step: report" in summary
    assert "boom" in summary
    assert "run.json" in summary
