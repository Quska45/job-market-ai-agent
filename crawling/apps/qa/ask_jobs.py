from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))

from job_market_ai_agent.qa.service import DEFAULT_JOBS_INPUT, answer_job_question  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask questions about collected job postings.")
    parser.add_argument("question", help="Question to ask about the collected job postings.")
    parser.add_argument("--input", default=DEFAULT_JOBS_INPUT)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--show-candidates", action="store_true")
    parser.add_argument("--no-llm", action="store_true", help="Only show search candidates without LLM answer.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        answer_job_question(
            args.question,
            input_path=Path(args.input),
            limit=args.limit,
            model=args.model,
            include_candidates=args.show_candidates,
            no_llm=args.no_llm,
        )
    )


if __name__ == "__main__":
    main()
