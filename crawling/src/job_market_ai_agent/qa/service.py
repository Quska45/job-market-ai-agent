from __future__ import annotations

from pathlib import Path

from job_market_ai_agent.qa.answer import answer_question_with_ollama, format_search_results
from job_market_ai_agent.qa.search import load_jobs, search_jobs


DEFAULT_JOBS_INPUT = "data/raw/saramin/latest.json"


def answer_job_question(
    question: str,
    input_path: Path = Path(DEFAULT_JOBS_INPUT),
    limit: int = 5,
    model: str = "qwen2.5:3b",
    include_candidates: bool = False,
    no_llm: bool = False,
) -> str:
    jobs = load_jobs(input_path)
    results = search_jobs(question, jobs, limit=limit)
    candidates = format_search_results(results)
    if no_llm:
        return candidates

    answer = answer_question_with_ollama(question, results, model=model)
    if include_candidates:
        return f"{candidates}\n\n{answer}"
    return answer
