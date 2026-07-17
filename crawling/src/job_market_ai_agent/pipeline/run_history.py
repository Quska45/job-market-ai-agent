from __future__ import annotations

import json
import subprocess
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Iterator


def utc_now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass(frozen=True)
class StepRecord:
    name: str
    status: str
    started_at: str
    finished_at: str | None = None
    duration_seconds: float | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
        }


@dataclass
class PipelineRunHistory:
    run_id: str
    run_dir: Path
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: str | None = None
    status: str = "running"
    failed_step: str | None = None
    error_message: str | None = None
    output_json: str | None = None
    report_path: str | None = None
    collected_jobs: int | None = None
    analyzed_jobs: int | None = None
    notified_channels: list[str] = field(default_factory=list)
    steps: list[StepRecord] = field(default_factory=list)

    @classmethod
    def create(cls, base_dir: Path, run_id: str | None = None) -> "PipelineRunHistory":
        actual_run_id = run_id or datetime.now().astimezone().strftime("%Y-%m-%d_%H%M%S")
        run_dir = base_dir / actual_run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        history = cls(run_id=actual_run_id, run_dir=run_dir)
        history.save()
        return history

    @contextmanager
    def step(self, name: str) -> Iterator[None]:
        started_at = utc_now_iso()
        start_time = perf_counter()
        self.log(f"step_start: {name}")
        try:
            yield
        except Exception as error:
            finished_at = utc_now_iso()
            duration = round(perf_counter() - start_time, 3)
            self.steps.append(
                StepRecord(
                    name=name,
                    status="failed",
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_seconds=duration,
                    error_message=str(error),
                )
            )
            self.mark_failed(name, error)
            raise
        else:
            finished_at = utc_now_iso()
            duration = round(perf_counter() - start_time, 3)
            self.steps.append(
                StepRecord(
                    name=name,
                    status="success",
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_seconds=duration,
                )
            )
            self.log(f"step_success: {name} ({duration}s)")
            self.save()

    def mark_success(self) -> None:
        self.status = "success"
        self.finished_at = utc_now_iso()
        self.save()

    def mark_failed(self, failed_step: str, error: BaseException) -> None:
        self.status = "failed"
        self.failed_step = failed_step
        self.error_message = str(error)
        self.finished_at = utc_now_iso()
        self.write_error(error)
        self.log(f"step_failed: {failed_step}: {error}")
        self.save()

    def log(self, message: str) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        line = f"[{utc_now_iso()}] {message}\n"
        (self.run_dir / "pipeline.log").open("a", encoding="utf-8").write(line)

    def write_error(self, error: BaseException) -> None:
        content = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        if isinstance(error, subprocess.CalledProcessError):
            content += "\n--- stdout ---\n"
            content += str(error.stdout or "")
            content += "\n--- stderr ---\n"
            content += str(error.stderr or "")
        (self.run_dir / "error.txt").write_text(content, encoding="utf-8")

    def save(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "run.json").write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "failed_step": self.failed_step,
            "error_message": self.error_message,
            "output_json": self.output_json,
            "report_path": self.report_path,
            "collected_jobs": self.collected_jobs,
            "analyzed_jobs": self.analyzed_jobs,
            "notified_channels": self.notified_channels,
            "steps": [step.to_dict() for step in self.steps],
        }


def build_failure_summary(history: PipelineRunHistory) -> str:
    return "\n".join(
        [
            "채용공고 파이프라인 실패",
            f"run_id: {history.run_id}",
            f"failed_step: {history.failed_step or 'unknown'}",
            f"error: {history.error_message or 'unknown'}",
            f"history: {history.run_dir / 'run.json'}",
        ]
    )
