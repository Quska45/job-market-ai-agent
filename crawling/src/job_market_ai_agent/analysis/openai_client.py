from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

from job_market_ai_agent.analysis.models import JobAnalysis
from job_market_ai_agent.analysis.prompts import SYSTEM_PROMPT, build_job_analysis_prompt


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.2"


class OpenAIConfigurationError(RuntimeError):
    pass


class OpenAIResponseError(RuntimeError):
    pass


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip().lstrip("\ufeff"), value.strip())


def analyze_job_with_openai(job: dict[str, Any], model: str | None = None) -> JobAnalysis:
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise OpenAIConfigurationError("OPENAI_API_KEY is required.")

    response = httpx.post(
        OPENAI_RESPONSES_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=_build_request_payload(job, model or os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL),
        timeout=60,
    )
    if response.status_code >= 400:
        raise OpenAIResponseError(f"OpenAI API error {response.status_code}: {response.text[:500]}")

    output_text = _extract_output_text(response.json())
    return JobAnalysis.model_validate_json(output_text)


def _build_request_payload(job: dict[str, Any], model: str) -> dict[str, Any]:
    return {
        "model": model,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_job_analysis_prompt(job)},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "job_analysis",
                "schema": _strict_json_schema(JobAnalysis.model_json_schema()),
                "strict": True,
            }
        },
    }




def _strict_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    schema = dict(schema)
    properties = schema.get("properties", {})
    schema["required"] = list(properties.keys())
    schema["additionalProperties"] = False
    return schema
def _extract_output_text(payload: dict[str, Any]) -> str:
    if "output_text" in payload and isinstance(payload["output_text"], str):
        return payload["output_text"]
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    raise OpenAIResponseError("OpenAI response did not contain output_text.")


def parse_analysis_json(text: str) -> JobAnalysis:
    return JobAnalysis.model_validate(json.loads(text))



