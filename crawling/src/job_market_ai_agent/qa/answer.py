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
        job = result.job
        company = (job.get("company") or {}).get("name") or ""
        title = job.get("title") or ""
        deadline = (job.get("dates") or {}).get("deadline_text") or ""
        url = job.get("url") or ""
        lines.append(f"{index}. [{result.score}] {company} | {title} | {deadline} | {url}")
    return "\n".join(lines)


def _system_prompt() -> str:
    return """You answer questions about collected job postings.
Use only the provided postings as evidence.
The user is an experienced developer with 8-9 years of professional experience.
Do not invent companies, deadlines, skills, URLs, majors, benefits, or requirements.
"""
