from __future__ import annotations

import json
import os
from typing import Any

import httpx
from pydantic import ValidationError

from job_market_ai_agent.analysis.models import JobAnalysis
from job_market_ai_agent.analysis.prompts import SYSTEM_PROMPT, build_job_analysis_prompt


DEFAULT_OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 600
DEFAULT_OLLAMA_MAX_CONTENT_CHARS = 6000


class OllamaResponseError(RuntimeError):
    pass


def analyze_job_with_ollama(
    job: dict[str, Any],
    model: str = DEFAULT_OLLAMA_MODEL,
    url: str = DEFAULT_OLLAMA_URL,
) -> JobAnalysis:
    timeout_seconds = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", DEFAULT_OLLAMA_TIMEOUT_SECONDS))
    max_content_chars = int(os.getenv("OLLAMA_MAX_CONTENT_CHARS", DEFAULT_OLLAMA_MAX_CONTENT_CHARS))
    try:
        response = httpx.post(
            url,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": build_job_analysis_prompt(
                            job,
                            max_content_chars=max_content_chars,
                        ),
                    },
                ],
                "stream": False,
                "format": JobAnalysis.model_json_schema(),
                "options": {"temperature": 0, "num_ctx": 8192},
            },
            timeout=timeout_seconds,
        )
    except httpx.ConnectError as error:
        raise OllamaResponseError(
            "Ollama server is not running. Install Ollama and run a model first."
        ) from error
    except httpx.TimeoutException as error:
        raise OllamaResponseError(
            f"Ollama model response exceeded {timeout_seconds:g} seconds. "
            "Use a smaller model or increase OLLAMA_TIMEOUT_SECONDS."
        ) from error

    if response.status_code >= 400:
        raise OllamaResponseError(f"Ollama API error {response.status_code}: {response.text[:500]}")

    payload = response.json()
    content = (payload.get("message") or {}).get("content")
    if not isinstance(content, str):
        raise OllamaResponseError("Ollama response did not contain message.content.")
    try:
        return JobAnalysis.model_validate_json(content)
    except ValidationError:
        return JobAnalysis.model_validate(json.loads(content))
