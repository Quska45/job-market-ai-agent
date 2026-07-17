from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from job_market_ai_agent.quality.report import (  # noqa: E402
    build_quality_report,
    format_quality_report,
    quality_report_to_dict,
    attach_job_quality,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report collected job data quality.")
    parser.add_argument("input", help="Path to a collected jobs JSON file.")
    parser.add_argument(
        "--write-back",
        action="store_true",
        help="Write _quality_report into the same JSON file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = Path(args.input)
    rows = _load_rows(path)
    report = build_quality_report(rows)
    print(format_quality_report(report))
    if args.write_back:
        _write_back_quality_report(path, rows, report)


def _load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if isinstance(payload, dict) and "jobs" in payload:
        payload = payload["jobs"]
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON array or object with jobs: {path}")
    return payload


def _write_back_quality_report(path: Path, rows: list[dict[str, Any]], report) -> None:
    payload = {
        "_quality_report": quality_report_to_dict(report),
        "jobs": attach_job_quality(rows),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()


