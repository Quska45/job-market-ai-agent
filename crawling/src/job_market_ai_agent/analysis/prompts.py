from __future__ import annotations

import json
from typing import Any

from job_market_ai_agent.analysis.models import JobAnalysis


SYSTEM_PROMPT = """You are a job posting analyst for experienced AI/software engineering roles.
Return only valid JSON matching the requested schema. Do not include markdown.
Use only the provided job posting content as evidence.
The target candidate is an experienced developer with 8-9 years of professional experience, not a beginner.
If a field cannot be inferred, use a conservative value and explain the evidence briefly.
"""


def build_job_analysis_prompt(job: dict[str, Any], max_content_chars: int | None = None) -> str:
    payload = _build_prompt_payload(job, max_content_chars=max_content_chars)
    return "\n".join(
        [
            "Analyze this job posting and return a JobAnalysis JSON object.",
            "",
            "Output schema:",
            json.dumps(JobAnalysis.model_json_schema(), ensure_ascii=False, indent=2),
            "",
            "Target candidate:",
            "- Experienced software developer with 8-9 years of professional experience.",
            "- Prefer roles needing ownership, system design, backend/data/AI engineering depth, leadership, or senior-level delivery.",
            "- Do not optimize the recommendation for entry-level or beginner roles.",
            "",
            "Classification guidance:",
            "- role_category: concise role family, e.g. AI Engineer, Backend Developer, Data Engineer.",
            "- seniority: one of Intern, Junior, Junior/Mid, Mid, Mid/Senior, Senior, Lead, Unknown.",
            "- required_skills: skills explicitly required by qualifications or main tasks.",
            "- preferred_skills: skills listed as preferred or advantageous.",
            "- main_tasks: concrete responsibilities from the posting.",
            "- fit_for_beginner: 0.0 means unsuitable for beginners, 1.0 means very beginner-friendly.",
            "- fit_for_8_9_year_developer: 0.0 means poor fit for an 8-9 year developer, 1.0 means strong fit.",
            "- career_fit_reason: short reason focused on 8-9 years of experience.",
            "- senior_keywords: phrases indicating seniority, ownership, architecture, scale, leadership, or advanced expertise.",
            "- evidence: short source phrases that justify the classification.",
            "",
            "Job posting:",
            json.dumps(payload, ensure_ascii=False, indent=2),
        ]
    )


def _build_prompt_payload(job: dict[str, Any], max_content_chars: int | None) -> dict[str, Any]:
    content = job.get("content") or {}
    description = _truncate_text(content.get("description"), max_content_chars)
    sections = _truncate_sections(content.get("sections") or {}, max_content_chars)
    return {
        "title": job.get("title"),
        "company": (job.get("company") or {}).get("name"),
        "location": job.get("location"),
        "job": job.get("job"),
        "employment": job.get("employment"),
        "dates": job.get("dates"),
        "description": description,
        "sections": sections,
        "image_count": len(content.get("image_urls", [])),
    }


def _truncate_sections(sections: dict[str, Any], max_content_chars: int | None) -> dict[str, str]:
    if max_content_chars is None:
        return {str(key): str(value) for key, value in sections.items()}
    per_section_limit = max(500, max_content_chars // max(len(sections), 1))
    return {str(key): _truncate_text(value, per_section_limit) for key, value in sections.items()}


def _truncate_text(value: Any, max_chars: int | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if max_chars is None or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n[TRUNCATED_FOR_LOCAL_ANALYSIS]"
