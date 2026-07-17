from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))

from job_market_ai_agent.notifications.discord import notify  # noqa: E402
from job_market_ai_agent.notifications.env import load_env_file  # noqa: E402
from job_market_ai_agent.pipeline.run_history import (  # noqa: E402
    PipelineRunHistory,
    build_failure_summary,
)
from job_market_ai_agent.reporting.export import default_output_path  # noqa: E402
from job_market_ai_agent.reporting.summary import build_notification_summary  # noqa: E402
from job_market_ai_agent.storage.latest import update_latest_json  # noqa: E402

DEFAULT_SEARCH_URL = (
    "https://www.saramin.co.kr/zf_user/jobs/list/domestic?"
    "cat_mcls=2&loc_mcd=105000,118000&search_optional_item=n&search_done=y&panel_count=y"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the daily job collection and analysis pipeline.")
    parser.add_argument("--keyword", default="AI")
    parser.add_argument("--max-jobs", type=int, default=10)
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--search-url", default=DEFAULT_SEARCH_URL)
    parser.add_argument("--provider", choices=["ollama", "openai"], default="ollama")
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--analysis-max-jobs", type=int, default=10)
    parser.add_argument("--report-format", choices=["csv", "markdown"], default="csv")
    parser.add_argument("--notify", action="append", choices=["console", "discord"], default=None)
    parser.add_argument("--skip-analysis", action="store_true")
    parser.add_argument("--retry-of", default=None, help="Run ID this execution retries.")
    return parser.parse_args()


def main() -> None:
    load_env_file(ROOT / ".env")
    args = parse_args()
    history = PipelineRunHistory.create(ROOT / "data" / "runs")
    notify_channels = args.notify or ["console"]
    output_json = _expected_output_path(args.keyword)
    history.output_json = str(output_json)
    history.retry_of = args.retry_of
    history.run_config = _build_run_config(args, notify_channels)
    history.save()

    try:
        with history.step("collect"):
            _run(
                [
                    sys.executable,
                    "apps/collector/collect_saramin.py",
                    "--keyword",
                    args.keyword,
                    "--max-jobs",
                    str(args.max_jobs),
                    "--max-pages",
                    str(args.max_pages),
                    "--delay",
                    str(args.delay),
                    "--search-url",
                    args.search_url,
                ],
                history,
            )
            history.collected_jobs = len(_load_jobs(output_json))

        with history.step("quality"):
            _run(
                [sys.executable, "apps/collector/report_quality.py", str(output_json), "--write-back"],
                history,
            )

        if not args.skip_analysis:
            with history.step("analyze"):
                _run(
                    [
                        sys.executable,
                        "apps/analyzer/analyze_jobs.py",
                        str(output_json),
                        "--provider",
                        args.provider,
                        "--model",
                        args.model,
                        "--max-jobs",
                        str(args.analysis_max_jobs),
                        "--write-back",
                    ],
                    history,
                )
                history.analyzed_jobs = _count_analyzed_jobs(output_json)
        else:
            history.analyzed_jobs = _count_analyzed_jobs(output_json)
            history.save()

        with history.step("report"):
            _run(
                [sys.executable, "apps/reporter/export_jobs.py", str(output_json), "--format", args.report_format],
                history,
            )
            history.report_path = str(default_output_path(output_json, args.report_format))

        with history.step("latest"):
            latest_path = update_latest_json(output_json, _latest_output_path())
            history.log(f"latest_updated: {latest_path}")
            print(f"latest_updated: {latest_path}")

        with history.step("notify"):
            summary = build_notification_summary(_load_jobs(output_json))
            sent_channels = notify(summary, notify_channels)
            history.notified_channels = sent_channels
            history.log(f"notification_sent: {','.join(sent_channels) if sent_channels else 'none'}")
            print(f"notification_sent: {','.join(sent_channels) if sent_channels else 'none'}")

        history.mark_success()
        print(f"pipeline_done: {output_json}")
        print(f"run_history: {history.run_dir / 'run.json'}")
    except Exception as error:
        _notify_failure(history, notify_channels)
        print(f"pipeline_failed: {history.run_dir / 'run.json'}")
        raise SystemExit(1) from error


def _build_run_config(args: argparse.Namespace, notify_channels: list[str]) -> dict[str, Any]:
    return {
        "keyword": args.keyword,
        "max_jobs": args.max_jobs,
        "max_pages": args.max_pages,
        "delay": args.delay,
        "search_url": args.search_url,
        "provider": args.provider,
        "model": args.model,
        "analysis_max_jobs": args.analysis_max_jobs,
        "report_format": args.report_format,
        "notify": notify_channels,
        "skip_analysis": args.skip_analysis,
    }


def _notify_failure(history: PipelineRunHistory, channels: list[str]) -> None:
    try:
        sent_channels = notify(build_failure_summary(history), channels)
        history.notified_channels = sent_channels
        history.log(f"failure_notification_sent: {','.join(sent_channels) if sent_channels else 'none'}")
        history.save()
    except Exception as notify_error:
        history.log(f"failure_notification_error: {notify_error}")
        history.save()


def _load_jobs(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as file:
        payload = json.load(file)
    if isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
        return payload["jobs"]
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Expected a JSON array or object with jobs: {path}")


def _count_analyzed_jobs(path: Path) -> int:
    return sum(1 for job in _load_jobs(path) if job.get("analysis"))


def _expected_output_path(keyword: str) -> Path:
    date_prefix = datetime.now().astimezone().strftime("%Y-%m-%d")
    safe_keyword = "".join(ch if ch.isalnum() else "_" for ch in keyword)
    return Path("data/raw/saramin") / f"{date_prefix}_{safe_keyword}.json"


def _latest_output_path() -> Path:
    return Path("data/raw/saramin/latest.json")


def _run(command: list[str], history: PipelineRunHistory) -> None:
    command_text = " ".join(command)
    history.log(f"running: {command_text}")
    print("running:", command_text)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.stdout:
        history.log(completed.stdout.rstrip())
        _safe_print(completed.stdout, end="")
    if completed.stderr:
        history.log(completed.stderr.rstrip())
        _safe_print(completed.stderr, end="", file=sys.stderr)


def _safe_print(value: str, end: str = "\n", file: TextIO | None = None) -> None:
    output = file or sys.stdout
    encoding = output.encoding or "utf-8"
    safe_value = value.encode(encoding, errors="replace").decode(encoding, errors="replace")
    print(safe_value, end=end, file=output)


if __name__ == "__main__":
    main()
