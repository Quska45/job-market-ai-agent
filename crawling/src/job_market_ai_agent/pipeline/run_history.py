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


def list_run_records(base_dir: Path, limit: int | None = None) -> list[dict[str, Any]]:
    if not base_dir.exists():
        return []
    records = []
    for run_json in sorted(base_dir.glob("*/run.json"), reverse=True):
        records.append(load_run_record(run_json.parent.name, base_dir))
    return records[:limit] if limit is not None else records


def load_run_record(run_id: str, base_dir: Path) -> dict[str, Any]:
    run_json = base_dir / run_id / "run.json"
    if not run_json.exists():
        raise FileNotFoundError(f"Run history not found: {run_json}")
    with run_json.open("r", encoding="utf-8") as file:
        return json.load(file)


def format_run_list(records: list[dict[str, Any]]) -> str:
    headers = ["run_id", "status", "failed_step", "collected", "analyzed", "started_at"]
    rows = [
        [
            _text(record.get("run_id")),
            _text(record.get("status")),
            _text(record.get("failed_step") or "-"),
            _text(record.get("collected_jobs") if record.get("collected_jobs") is not None else "-"),
            _text(record.get("analyzed_jobs") if record.get("analyzed_jobs") is not None else "-"),
            _text(record.get("started_at")),
        ]
        for record in records
    ]
    return _format_table(headers, rows)


def format_run_detail(record: dict[str, Any]) -> str:
    lines = [
        f"run_id: {_text(record.get('run_id'))}",
        f"status: {_text(record.get('status'))}",
        f"started_at: {_text(record.get('started_at'))}",
        f"finished_at: {_text(record.get('finished_at'))}",
        f"failed_step: {_text(record.get('failed_step') or '-')}",
        f"error_message: {_text(record.get('error_message') or '-')}",
        f"output_json: {_text(record.get('output_json') or '-')}",
        f"report_path: {_text(record.get('report_path') or '-')}",
        f"collected_jobs: {_text(record.get('collected_jobs') if record.get('collected_jobs') is not None else '-')}",
        f"analyzed_jobs: {_text(record.get('analyzed_jobs') if record.get('analyzed_jobs') is not None else '-')}",
        f"notified_channels: {', '.join(record.get('notified_channels') or []) or '-'}",
        "steps:",
    ]
    for step in record.get("steps") or []:
        duration = step.get("duration_seconds")
        duration_text = f"{duration}s" if duration is not None else "-"
        error_text = f" | error={step.get('error_message')}" if step.get("error_message") else ""
        lines.append(f"- {step.get('name')}: {step.get('status')} ({duration_text}){error_text}")
    return "\n".join(lines)


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


def _format_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "No run history found."
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row, strict=True)]
    lines = ["  ".join(header.ljust(width) for header, width in zip(headers, widths, strict=True))]
    lines.append("  ".join("-" * width for width in widths))
    for row in rows:
        lines.append("  ".join(value.ljust(width) for value, width in zip(row, widths, strict=True)))
    return "\n".join(lines)


def _text(value: Any) -> str:
    return "" if value is None else str(value)
