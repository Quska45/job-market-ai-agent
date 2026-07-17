from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from job_market_ai_agent.qa.query import (
    DEVELOPER_ROLE_ALIASES,
    NON_DEVELOPER_ROLE_ALIASES,
    ROLE_KEYWORDS,
    QueryIntent,
    classify_deadline_text,
    parse_query_intent,
)


@dataclass(frozen=True)
class JobSearchResult:
    job: dict[str, Any]
    score: int
    matched_terms: list[str]


def load_jobs(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as file:
        payload = json.load(file)
    if isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
        return payload["jobs"]
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Expected a JSON array or object with jobs: {path}")


def search_jobs(query: str, jobs: Iterable[dict[str, Any]], limit: int = 5) -> list[JobSearchResult]:
    intent = parse_query_intent(query)
    results = []
    for job in jobs:
        if not _matches_required_filters(job, intent):
            continue
        score, matched_terms = _score_job(job, intent)
        if score > 0:
            results.append(JobSearchResult(job=job, score=score, matched_terms=matched_terms))
    return sorted(results, key=lambda result: result.score, reverse=True)[:limit]


def summarize_job_for_qa(job: dict[str, Any]) -> dict[str, Any]:
    analysis = job.get("analysis") or {}
    content = job.get("content") or {}
    return {
        "source_job_id": job.get("source_job_id"),
        "company": (job.get("company") or {}).get("name"),
        "title": job.get("title"),
        "url": job.get("url"),
        "location": job.get("location"),
        "employment": job.get("employment"),
        "dates": job.get("dates"),
        "skills": job.get("skills") or [],
        "analysis": {
            "role_category": analysis.get("role_category"),
            "seniority": analysis.get("seniority"),
            "required_skills": analysis.get("required_skills") or [],
            "preferred_skills": analysis.get("preferred_skills") or [],
            "main_tasks": analysis.get("main_tasks") or [],
            "fit_for_8_9_year_developer": analysis.get("fit_for_8_9_year_developer"),
            "career_fit_reason": analysis.get("career_fit_reason"),
            "summary": analysis.get("summary"),
        },
        "description_excerpt": _truncate(content.get("description"), 900),
    }


def _matches_required_filters(job: dict[str, Any], intent: QueryIntent) -> bool:
    searchable = _searchable_text(job)
    if intent.regions and not any(region.lower() in searchable for region in intent.regions):
        return False
    if intent.excluded_roles and any(_matches_excluded_role(job, role) for role in intent.excluded_roles):
        return False
    if intent.deadline_types:
        dates = job.get("dates") or {}
        deadline_type = classify_deadline_text(dates.get("deadline_text"), dates.get("deadline"))
        if deadline_type not in intent.deadline_types:
            return False
    return True


def _score_job(job: dict[str, Any], intent: QueryIntent) -> tuple[int, list[str]]:
    searchable = _searchable_text(job)
    matched_terms = [term for term in intent.terms if term in searchable]
    matched_terms.extend([region.lower() for region in intent.regions if region.lower() in searchable])
    matched_terms.extend([skill for skill in intent.skills if skill in searchable])
    matched_terms.extend([role for role in intent.role_terms if role in searchable])
    matched_terms = sorted(set(matched_terms))

    score = len(matched_terms)
    if not matched_terms and not (intent.experienced and job.get("analysis")):
        return 0, []

    title = str(job.get("title") or "").lower()
    analysis = job.get("analysis") or {}
    high_value_text = " ".join(
        [
            title,
            str((job.get("company") or {}).get("name") or ""),
            str((job.get("location") or {}).get("summary") or ""),
            str(analysis.get("role_category") or ""),
            " ".join(analysis.get("required_skills") or []),
            " ".join(analysis.get("preferred_skills") or []),
        ]
    ).lower()
    score += sum(2 for term in matched_terms if term in high_value_text)

    score += _structured_bonus(job, intent)
    score += _developer_role_bonus(job, intent)
    fit_score = analysis.get("fit_for_8_9_year_developer")
    if isinstance(fit_score, int | float):
        score += round(float(fit_score) * (5 if intent.experienced else 3))
    elif intent.require_analyzed:
        score -= 2
    return score, matched_terms


def _structured_bonus(job: dict[str, Any], intent: QueryIntent) -> int:
    searchable = _searchable_text(job)
    bonus = 0
    bonus += 4 * sum(1 for region in intent.regions if region.lower() in searchable)
    bonus += 3 * sum(1 for skill in intent.skills if skill in searchable)
    bonus += 3 * sum(1 for role in intent.role_terms if _matches_role(job, role))
    if intent.experienced and job.get("analysis"):
        bonus += 2
    return bonus


def _developer_role_bonus(job: dict[str, Any], intent: QueryIntent) -> int:
    if not intent.prefer_developer_roles:
        return 0
    searchable = _role_searchable_text(job)
    bonus = 0
    if any(alias in searchable for alias in DEVELOPER_ROLE_ALIASES):
        bonus += 5
    if any(alias in searchable for alias in NON_DEVELOPER_ROLE_ALIASES):
        bonus -= 6
    if intent.role_terms and not any(_matches_role(job, role) for role in intent.role_terms):
        bonus -= 4
    return bonus


def _matches_role(job: dict[str, Any], role: str) -> bool:
    aliases = ROLE_KEYWORDS.get(role, [])
    if not aliases:
        return False
    searchable = _role_searchable_text(job)
    return any(alias in searchable for alias in aliases)


def _matches_excluded_role(job: dict[str, Any], role: str) -> bool:
    aliases = ROLE_KEYWORDS.get(role, [])
    if not aliases:
        return False
    searchable = _strict_role_searchable_text(job)
    return any(alias in searchable for alias in aliases)


def _role_searchable_text(job: dict[str, Any]) -> str:
    analysis = job.get("analysis") or {}
    job_info = job.get("job") or {}
    content = job.get("content") or {}
    sections = content.get("sections") or {}
    parts = [
        str(job.get("title") or ""),
        str(job_info.get("category") or ""),
        " ".join(job_info.get("sub_categories") or []),
        " ".join(job.get("skills") or []),
        str(analysis.get("role_category") or ""),
        str(analysis.get("seniority") or ""),
        " ".join(analysis.get("required_skills") or []),
        " ".join(analysis.get("preferred_skills") or []),
        " ".join(analysis.get("main_tasks") or []),
        str(analysis.get("summary") or ""),
        str(sections.get("core") or ""),
    ]
    return " ".join(parts).lower()


def _strict_role_searchable_text(job: dict[str, Any]) -> str:
    analysis = job.get("analysis") or {}
    job_info = job.get("job") or {}
    parts = [
        str(job.get("title") or ""),
        str(job_info.get("category") or ""),
        " ".join(job_info.get("sub_categories") or []),
        " ".join(job.get("skills") or []),
        str(analysis.get("role_category") or ""),
        " ".join(analysis.get("required_skills") or []),
        " ".join(analysis.get("main_tasks") or []),
    ]
    return " ".join(parts).lower()


def _searchable_text(job: dict[str, Any]) -> str:
    parts: list[str] = []
    _collect_text(job, parts)
    return " ".join(parts).lower()


def _collect_text(value: Any, parts: list[str]) -> None:
    if value is None:
        return
    if isinstance(value, str):
        parts.append(value)
        return
    if isinstance(value, int | float | bool):
        parts.append(str(value))
        return
    if isinstance(value, dict):
        for child in value.values():
            _collect_text(child, parts)
        return
    if isinstance(value, list):
        for child in value:
            _collect_text(child, parts)


def _truncate(value: Any, max_chars: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."
