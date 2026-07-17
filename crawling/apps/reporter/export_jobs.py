from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from job_market_ai_agent.reporting.export import default_output_path, write_report  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export analyzed job postings as a table report.")
    parser.add_argument("input", help="Path to collected jobs JSON.")
    parser.add_argument("--format", choices=["csv", "markdown"], default="csv")
    parser.add_argument("--output", default=None, help="Output report path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else default_output_path(input_path, args.format)
    written_path = write_report(input_path, output_path, args.format)
    print(f"report_written: {written_path}")


if __name__ == "__main__":
    main()
