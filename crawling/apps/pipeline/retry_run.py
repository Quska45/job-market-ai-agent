from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))

from job_market_ai_agent.pipeline.run_history import build_retry_command, load_run_record  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retry a previous pipeline run.")
    parser.add_argument("run_id", help="Run ID to retry.")
    parser.add_argument("--runs-dir", default="data/runs", help="Directory containing pipeline runs.")
    parser.add_argument("--dry-run", action="store_true", help="Print the retry command without running it.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = load_run_record(args.run_id, Path(args.runs_dir))
    command = build_retry_command(
        record,
        python_executable=sys.executable,
        pipeline_script="apps/pipeline/daily_job_pipeline.py",
    )
    print("retry_command:", " ".join(command))
    if args.dry_run:
        return
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
