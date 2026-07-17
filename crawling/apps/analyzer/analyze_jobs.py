from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from job_market_ai_agent.analysis.ollama_client import (  # noqa: E402
    OllamaResponseError,
    analyze_job_with_ollama,
)
from job_market_ai_agent.analysis.openai_client import (  # noqa: E402
    OpenAIConfigurationError,
    OpenAIResponseError,
    analyze_job_with_openai,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze collected jobs with an LLM provider.")
    parser.add_argument("input", help="Path to collected jobs JSON.")
    parser.add_argument("--max-jobs", type=int, default=1, help="Maximum jobs to analyze.")
    parser.add_argument("--provider", choices=["openai", "ollama"], default="ollama")
    parser.add_argument("--model", default=None, help="Model name for the selected provider.")
    parser.add_argument("--force", action="store_true", help="Re-analyze jobs that already have analysis.")
    parser.add_argument("--write-back", action="store_true", help="Write analysis into the same JSON file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = Path(args.input)
    payload, jobs = _load_payload(path)

    analyzed_count = 0
    for job in jobs:
        if analyzed_count >= args.max_jobs:
            break
        if job.get("analysis") and not args.force:
            continue
        try:
            analysis = _analyze_job(job, provider=args.provider, model=args.model)
        except (OpenAIConfigurationError, OpenAIResponseError, OllamaResponseError) as error:
            raise SystemExit(f"analysis failed: {error}") from error
        job["analysis"] = analysis.model_dump(mode="json")
        analyzed_count += 1
        print(f"analyzed {job.get('source_job_id')} | {job.get('title')}")
        if args.write_back:
            _write_payload(path, payload, jobs)

    print(f"analyzed_count: {analyzed_count}")
    if args.write_back:
        _write_payload(path, payload, jobs)


def _analyze_job(job: dict[str, Any], provider: str, model: str | None):
    if provider == "openai":
        return analyze_job_with_openai(job, model=model)
    if provider == "ollama":
        return analyze_job_with_ollama(job, model=model or "qwen2.5:3b")
    raise ValueError(f"Unsupported provider: {provider}")


def _load_payload(path: Path) -> tuple[dict[str, Any] | list[dict[str, Any]], list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
        return payload, payload["jobs"]
    if isinstance(payload, list):
        return payload, payload
    raise ValueError(f"Expected a JSON array or object with jobs: {path}")


def _write_payload(
    path: Path,
    payload: dict[str, Any] | list[dict[str, Any]],
    jobs: list[dict[str, Any]],
) -> None:
    if isinstance(payload, dict):
        payload["jobs"] = jobs
        output = payload
    else:
        output = jobs
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
