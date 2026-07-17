from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))

from job_market_ai_agent.qa.answer import answer_question_with_ollama, format_search_results  # noqa: E402
from job_market_ai_agent.qa.search import load_jobs, search_jobs  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask questions about collected job postings.")
    parser.add_argument("question", help="Question to ask about the collected job postings.")
    parser.add_argument("--input", default="data/raw/saramin/2026-07-17_AI.json")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--show-candidates", action="store_true")
    parser.add_argument("--no-llm", action="store_true", help="Only show search candidates without LLM answer.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    jobs = load_jobs(Path(args.input))
    results = search_jobs(args.question, jobs, limit=args.limit)
    if args.show_candidates or args.no_llm:
        print(format_search_results(results))
    if args.no_llm:
        return
    print(answer_question_with_ollama(args.question, results, model=args.model))


if __name__ == "__main__":
    main()
