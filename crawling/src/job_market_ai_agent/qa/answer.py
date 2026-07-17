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
        return "관련 채용공고를 찾지 못했습니다. 질문의 지역, 직무, 기술 키워드를 조금 더 구체적으로 입력해 주세요."

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
            f"Ollama 답변 생성이 {timeout_seconds:g}초 안에 끝나지 않았습니다. "
            "검색 후보를 먼저 확인하거나 질문을 더 짧게 입력해 주세요."
        ) from error
    except httpx.ConnectError as error:
        raise QAResponseError("Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인해 주세요.") from error

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
    if not results:
        return "검색된 공고가 없습니다."
    lines = ["검색 후보:"]
    for index, result in enumerate(results, start=1):
        lines.extend(_format_search_result(index, result))
    return "\n".join(lines)


def _format_search_result(index: int, result: JobSearchResult) -> list[str]:
    job = result.job
    company = job.get("company") or {}
    location = job.get("location") or {}
    job_info = job.get("job") or {}
    employment = job.get("employment") or {}
    dates = job.get("dates") or {}
    analysis = job.get("analysis") or {}

    title = _clean(job.get("title")) or "제목 없음"
    company_name = _clean(company.get("name")) or "회사명 없음"
    deadline = _clean(dates.get("deadline_text")) or _clean(dates.get("deadline")) or "마감 정보 없음"
    posted_at = _clean(dates.get("posted_at")) or "시작일 없음"
    deadline_at = _clean(dates.get("deadline")) or "마감일 없음"
    matched = _join(result.matched_terms, limit=6) or "-"
    skills = _join(job.get("skills"), limit=8)
    required_skills = _join(analysis.get("required_skills"), limit=6)
    preferred_skills = _join(analysis.get("preferred_skills"), limit=6)
    sub_categories = _join(job_info.get("sub_categories"), limit=6)
    main_tasks = _join(analysis.get("main_tasks"), limit=3, max_item_chars=45)
    fit = _format_fit_score(analysis.get("fit_for_8_9_year_developer"))
    summary = _truncate(analysis.get("summary") or (job.get("content") or {}).get("summary"), 180)
    reason = _truncate(analysis.get("career_fit_reason"), 160)

    lines = [
        "",
        f"{index}. [점수 {result.score}] {company_name} | {title}",
        f"- 지역: {_clean(location.get('summary')) or '-'}",
        f"- 주소: {_clean(location.get('address')) or '-'}",
        f"- 직무: {_clean(job_info.get('category')) or '-'} / {sub_categories or '-'}",
        f"- 경력/고용: {_clean(employment.get('experience')) or '-'} / {_clean(employment.get('type')) or '-'}",
        f"- 기간: {posted_at} -> {deadline_at} ({deadline})",
        f"- 기업: {_clean(company.get('size_type')) or '-'} / {_clean(company.get('employee_count')) or '-'}",
        f"- 기술: {skills or required_skills or '-'}",
        f"- 우대/관련: {preferred_skills or '-'}",
        f"- 주요업무: {main_tasks or '-'}",
        f"- 8-9년차 적합도: {fit}",
        f"- 매칭: {matched}",
    ]
    if reason:
        lines.append(f"- 적합 이유: {reason}")
    if summary:
        lines.append(f"- 요약: {summary}")
    lines.append(f"- URL: {_clean(job.get('url')) or '-'}")
    return lines


def _join(value: Any, limit: int, max_item_chars: int = 30) -> str | None:
    if not isinstance(value, list):
        return None
    items = [_truncate(item, max_item_chars) for item in value if _clean(item)]
    visible = [item for item in items if item][:limit]
    if not visible:
        return None
    suffix = f" 외 {len(items) - limit}개" if len(items) > limit else ""
    return ", ".join(visible) + suffix


def _format_fit_score(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{round(float(value) * 100)}%"
    return "분석 없음"


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
