from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))

from job_market_ai_agent.pipeline.run_history import format_run_detail, load_run_record  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show one pipeline run history record.")
    parser.add_argument("run_id", help="Run ID to show, for example 2026-07-18_090000.")
    parser.add_argument("--runs-dir", default="data/runs", help="Directory containing pipeline runs.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = load_run_record(args.run_id, Path(args.runs_dir))
    print(format_run_detail(record))


if __name__ == "__main__":
    main()
