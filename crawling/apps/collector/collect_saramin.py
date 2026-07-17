from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from job_market_ai_agent.collectors.saramin import SaraminCollector
from job_market_ai_agent.storage.json_store import save_models_json
from job_market_ai_agent.storage.latest import default_latest_path, update_latest_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect public Saramin job postings.")
    parser.add_argument("--keyword", required=True, help="Search keyword, for example AI or Python.")
    parser.add_argument("--max-jobs", type=int, default=20, help="Maximum job detail pages to collect.")
    parser.add_argument("--max-pages", type=int, default=1, help="Maximum search result pages to scan.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds.")
    parser.add_argument(
        "--search-url",
        default=None,
        help="Optional Saramin search result URL copied from the browser.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/raw/saramin",
        help="Directory where the JSON result will be saved.",
    )
    parser.add_argument(
        "--latest-path",
        default=None,
        help="Path to update with the latest collected JSON. Defaults to <output-dir>/latest.json.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    collector = SaraminCollector(
        keyword=args.keyword,
        max_jobs=args.max_jobs,
        max_pages=args.max_pages,
        delay_seconds=args.delay,
        search_url=args.search_url,
    )
    try:
        postings = collector.collect()
    finally:
        collector.close()

    date_prefix = datetime.now().astimezone().strftime("%Y-%m-%d")
    safe_keyword = "".join(ch if ch.isalnum() else "_" for ch in args.keyword)
    output_dir = Path(args.output_dir)
    output_path = output_dir / f"{date_prefix}_{safe_keyword}.json"
    save_models_json(output_path, postings)
    latest_path = Path(args.latest_path) if args.latest_path else default_latest_path(output_dir)
    update_latest_json(output_path, latest_path)
    print(f"saved {len(postings)} postings to {output_path}")
    print(f"updated latest postings at {latest_path}")


if __name__ == "__main__":
    main()



