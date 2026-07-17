from __future__ import annotations

import argparse
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
from typing import Any

from job_market_ai_agent.quality.report import build_quality_report, format_quality_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report collected job data quality.")
    parser.add_argument("input", help="Path to a collected jobs JSON file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = _load_rows(Path(args.input))
    report = build_quality_report(rows)
    print(format_quality_report(report))


def _load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON array: {path}")
    return payload


if __name__ == "__main__":
    main()



