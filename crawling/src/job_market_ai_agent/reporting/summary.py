from __future__ import annotations

from typing import Any


def build_notification_summary(jobs: list[dict[str, Any]], top_n: int = 3) -> str:
    analyzed_jobs = [job for job in jobs if job.get("analysis")]
    top_jobs = sorted(
        analyzed_jobs,
        key=lambda job: _score(job),
        reverse=True,
    )[:top_n]

    lines = [
        f"collected_jobs: {len(jobs)}",
        f"analyzed_jobs: {len(analyzed_jobs)}",
        "top_fit_jobs:",
    ]
    if not top_jobs:
        lines.append("- none")
        return "\n".join(lines)

    for job in top_jobs:
        analysis = job.get("analysis") or {}
        company = (job.get("company") or {}).get("name") or ""
        title = job.get("title") or ""
        score = _score(job)
        deadline_text = (job.get("dates") or {}).get("deadline_text") or ""
        lines.append(f"- {company} | {title} | fit={score:.2f} | deadline={deadline_text}")
    return "\n".join(lines)


def _score(job: dict[str, Any]) -> float:
    value = (job.get("analysis") or {}).get("fit_for_8_9_year_developer")
    if isinstance(value, int | float):
        return float(value)
    return 0.0
