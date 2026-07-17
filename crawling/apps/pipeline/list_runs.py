from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))

from job_market_ai_agent.pipeline.run_history import format_run_list, list_run_records  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List pipeline run history.")
    parser.add_argument("--runs-dir", default="data/runs", help="Directory containing pipeline runs.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of runs to show.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = list_run_records(Path(args.runs_dir), limit=args.limit)
    print(format_run_list(records))


if __name__ == "__main__":
    main()
