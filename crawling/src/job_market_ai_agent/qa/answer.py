from __future__ import annotations

import json
import os
from typing import Any

import httpx

from job_market_ai_agent.qa.search import JobSearchResult, summarize_job_for_qa


DEFAULT_OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_QA_MODEL = "qwen2.5:3b"
DEFAULT_QA_TIMEOUT_SECONDS = 180


class QAResponseError(RuntimeError):
    pass


def answer_question_with_ollama(
    question: str,
    results: list[JobSearchResult],
    model: str = DEFAULT_QA_MODEL,
    url: str = DEFAULT_OLLAMA_URL,
) -> str:
    if not results:
        return "\uad00\ub828 \ucc44\uc6a9\uacf5\uace0\ub97c \ucc3e\uc9c0 \ubabb\ud588\uc2b5\ub2c8\ub2e4. \uc9c8\ubb38\uc758 \uc9c0\uc5ed, \uc9c1\ubb34, \uae30\uc220 \ud0a4\uc6cc\ub4dc\ub97c \uc870\uae08 \ub354 \uad6c\uccb4\uc801\uc73c\ub85c \uc785\ub825\ud574 \uc8fc\uc138\uc694."

    timeout_seconds = float(os.getenv("OLLAMA_QA_TIMEOUT_SECONDS", DEFAULT_QA_TIMEOUT_SECONDS))
    try:
        response = httpx.post(
            url,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": _system_prompt()},
                    {"role": "user", "content": build_qa_prompt(question, results)},
                ],
                "stream": False,
                "options": {"temperature": 0, "num_ctx": 4096},
            },
            timeout=timeout_seconds,
        )
    except httpx.TimeoutException as error:
        raise QAResponseError(
            f"Ollama \ub2f5\ubcc0 \uc0dd\uc131\uc774 {timeout_seconds:g}\ucd08 \uc548\uc5d0 \ub05d\ub098\uc9c0 \uc54a\uc558\uc2b5\ub2c8\ub2e4. "
            "\uac80\uc0c9 \ud6c4\ubcf4\ub97c \uba3c\uc800 \ud655\uc778\ud558\uac70\ub098 \uc9c8\ubb38\uc744 \ub354 \uc9e7\uac8c \uc785\ub825\ud574 \uc8fc\uc138\uc694."
        ) from error
    except httpx.ConnectError as error:
        raise QAResponseError("Ollama \uc11c\ubc84\uc5d0 \uc5f0\uacb0\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4. Ollama\uac00 \uc2e4\ud589 \uc911\uc778\uc9c0 \ud655\uc778\ud574 \uc8fc\uc138\uc694.") from error

    if response.status_code >= 400:
        raise QAResponseError(f"Ollama API error {response.status_code}: {response.text[:500]}")
    payload = response.json()
    content = (payload.get("message") or {}).get("content")
    if not isinstance(content, str):
        raise QAResponseError("Ollama response did not contain message.content.")
    return content.strip()


def build_qa_prompt(question: str, results: list[JobSearchResult]) -> str:
    evidence = [
        {
            "score": result.score,
            "matched_terms": result.matched_terms,
            "job": summarize_job_for_qa(result.job),
        }
        for result in results
    ]
    return "\n".join(
        [
            "Question:",
            question,
            "",
            "Candidate job postings:",
            json.dumps(evidence, ensure_ascii=False, indent=2),
            "",
            "Answer in Korean. Include company, title, reason, deadline, and URL when recommending jobs.",
            "For recommendation reasons, use only these fields: title, location, employment, dates, skills, analysis, and description_excerpt.",
            "Do not mention majors, education details, benefits, company facts, or requirements unless they appear explicitly in the provided JSON.",
            "If the evidence is insufficient, say what is missing instead of inventing details.",
        ]
    )


def format_search_results(results: list[JobSearchResult]) -> str:
    return format_search_summary_results(results)


def format_search_summary_results(results: list[JobSearchResult]) -> str:
    if not results:
        return "\uac80\uc0c9\ub41c \uacf5\uace0\uac00 \uc5c6\uc2b5\ub2c8\ub2e4."
    lines = ["\uac80\uc0c9 \ud6c4\ubcf4 Top 3:"]
    for index, result in enumerate(results[:3], start=1):
        lines.extend(_format_search_summary_result(index, result))
    lines.append("")
    lines.append("\uc0c1\uc138 \uc815\ubcf4: `detail \ubc88\ud638` \ub610\ub294 `!job detail \ubc88\ud638`")
    return "\n".join(lines)


def format_search_detail_result(result: JobSearchResult, index: int | None = None) -> str:
    header_index = f"{index}. " if index is not None else ""
    return "\n".join(_format_search_detail_lines(header_index, result))


def _format_search_summary_result(index: int, result: JobSearchResult) -> list[str]:
    job = result.job
    company = job.get("company") or {}
    location = job.get("location") or {}
    employment = job.get("employment") or {}
    dates = job.get("dates") or {}
    analysis = job.get("analysis") or {}

    title = _clean(job.get("title")) or "\uc81c\ubaa9 \uc5c6\uc74c"
    company_name = _clean(company.get("name")) or "\ud68c\uc0ac\uba85 \uc5c6\uc74c"
    deadline = _clean(dates.get("deadline_text")) or _clean(dates.get("deadline")) or "\ub9c8\uac10 \uc815\ubcf4 \uc5c6\uc74c"
    skills = _join(job.get("skills"), limit=5) or _join(analysis.get("required_skills"), limit=5) or "-"
    fit = _format_fit_score(analysis.get("fit_for_8_9_year_developer"))

    return [
        "",
        f"{index}. {company_name} | {title}",
        f"- \uc9c0\uc5ed: {_clean(location.get('summary')) or '-'}",
        f"- \uacbd\ub825: {_clean(employment.get('experience')) or '-'}",
        f"- \ub9c8\uac10: {deadline}",
        f"- \uae30\uc220: {skills}",
        f"- 8-9\ub144\ucc28 \uc801\ud569\ub3c4: {fit}",
        f"- URL: {_clean(job.get('url')) or '-'}",
    ]


def _format_search_detail_lines(header_index: str, result: JobSearchResult) -> list[str]:
    job = result.job
    company = job.get("company") or {}
    location = job.get("location") or {}
    job_info = job.get("job") or {}
    employment = job.get("employment") or {}
    dates = job.get("dates") or {}
    analysis = job.get("analysis") or {}

    title = _clean(job.get("title")) or "\uc81c\ubaa9 \uc5c6\uc74c"
    company_name = _clean(company.get("name")) or "\ud68c\uc0ac\uba85 \uc5c6\uc74c"
    deadline = _clean(dates.get("deadline_text")) or _clean(dates.get("deadline")) or "\ub9c8\uac10 \uc815\ubcf4 \uc5c6\uc74c"
    posted_at = _clean(dates.get("posted_at")) or "\uc2dc\uc791\uc77c \uc5c6\uc74c"
    deadline_at = _clean(dates.get("deadline")) or "\ub9c8\uac10\uc77c \uc5c6\uc74c"
    matched = _join(result.matched_terms, limit=6) or "-"
    skills = _join(job.get("skills"), limit=8)
    required_skills = _join(analysis.get("required_skills"), limit=6)
    preferred_skills = _join(analysis.get("preferred_skills"), limit=6)
    sub_categories = _join(job_info.get("sub_categories"), limit=6)
    main_tasks = _join(analysis.get("main_tasks"), limit=4, max_item_chars=55)
    fit = _format_fit_score(analysis.get("fit_for_8_9_year_developer"))
    summary = _truncate(analysis.get("summary") or (job.get("content") or {}).get("summary"), 320)
    reason = _truncate(analysis.get("career_fit_reason"), 240)

    lines = [
        f"{header_index}{company_name} | {title}",
        f"- \uc9c0\uc5ed: {_clean(location.get('summary')) or '-'}",
        f"- \uc8fc\uc18c: {_clean(location.get('address')) or '-'}",
        f"- \uc9c1\ubb34: {_clean(job_info.get('category')) or '-'} / {sub_categories or '-'}",
        f"- \uacbd\ub825/\uace0\uc6a9: {_clean(employment.get('experience')) or '-'} / {_clean(employment.get('type')) or '-'}",
        f"- \uae30\uac04: {posted_at} -> {deadline_at} ({deadline})",
        f"- \uae30\uc5c5: {_clean(company.get('size_type')) or '-'} / {_clean(company.get('employee_count')) or '-'}",
        f"- \uae30\uc220: {skills or required_skills or '-'}",
        f"- \uc6b0\ub300/\uad00\ub828: {preferred_skills or '-'}",
        f"- \uc8fc\uc694\uc5c5\ubb34: {main_tasks or '-'}",
        f"- 8-9\ub144\ucc28 \uc801\ud569\ub3c4: {fit}",
        f"- \ub9e4\uce6d: {matched}",
    ]
    if reason:
        lines.append(f"- \uc801\ud569 \uc774\uc720: {reason}")
    if summary:
        lines.append(f"- \uc694\uc57d: {summary}")
    lines.append(f"- URL: {_clean(job.get('url')) or '-'}")
    return lines


def _join(value: Any, limit: int, max_item_chars: int = 30) -> str | None:
    if not isinstance(value, list):
        return None
    items = [_truncate(item, max_item_chars) for item in value if _clean(item)]
    visible = [item for item in items if item][:limit]
    if not visible:
        return None
    suffix = f" \uc678 {len(items) - limit}\uac1c" if len(items) > limit else ""
    return ", ".join(visible) + suffix


def _format_fit_score(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{round(float(value) * 100)}%"
    return "\ubd84\uc11d \uc5c6\uc74c"


def _truncate(value: Any, max_chars: int) -> str | None:
    text = _clean(value)
    if text is None:
        return None
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def _system_prompt() -> str:
    return """You answer questions about collected job postings.
Use only the provided postings as evidence.
The user is an experienced developer with 8-9 years of professional experience.
Do not invent companies, deadlines, skills, URLs, majors, benefits, or requirements.
"""
