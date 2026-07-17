import json
import subprocess

import pytest

from job_market_ai_agent.pipeline.run_history import PipelineRunHistory, build_failure_summary


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
