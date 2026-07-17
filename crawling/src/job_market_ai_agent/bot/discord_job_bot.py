from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from job_market_ai_agent.notifications.env import load_env_file
from job_market_ai_agent.qa.answer import (
    answer_question_with_ollama,
    format_search_detail_result,
    format_search_summary_results,
)
from job_market_ai_agent.qa.search import JobSearchResult, load_jobs, search_jobs
from job_market_ai_agent.qa.service import DEFAULT_JOBS_INPUT, answer_job_question


@dataclass(frozen=True)
class DiscordBotConfig:
    token: str
    command_prefix: str = "!job"
    input_path: Path = Path(DEFAULT_JOBS_INPUT)
    limit: int = 3
    model: str = "qwen2.5:3b"
    respond_to_all: bool = False


@dataclass(frozen=True)
class DiscordJobCommand:
    question: str
    use_llm: bool = False
    detail_index: int | None = None


class DiscordBotConfigurationError(RuntimeError):
    pass


def load_discord_bot_config(env_path: Path = Path(".env")) -> DiscordBotConfig:
    load_env_file(env_path)
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise DiscordBotConfigurationError("DISCORD_BOT_TOKEN is required in .env or environment.")
    return DiscordBotConfig(
        token=token,
        command_prefix=os.getenv("DISCORD_BOT_COMMAND_PREFIX", "!job"),
        input_path=Path(os.getenv("JOB_QA_INPUT", DEFAULT_JOBS_INPUT)),
        limit=int(os.getenv("JOB_QA_LIMIT", "3")),
        model=os.getenv("JOB_QA_MODEL", "qwen2.5:3b"),
        respond_to_all=_read_bool_env("DISCORD_BOT_RESPOND_TO_ALL", default=False),
    )


def extract_job_question(content: str, command_prefix: str = "!job") -> str | None:
    command = parse_job_command(content, command_prefix)
    return command.question if command else None


def parse_job_command(
    content: str,
    command_prefix: str = "!job",
    respond_to_all: bool = False,
) -> DiscordJobCommand | None:
    stripped = content.strip()
    if not stripped:
        return None
    if stripped.startswith(command_prefix):
        question = stripped[len(command_prefix) :].strip()
    elif respond_to_all:
        question = stripped
    else:
        return None
    if not question:
        return None

    detail_index = _parse_detail_index(question)
    if detail_index is not None:
        return DiscordJobCommand(question="", detail_index=detail_index)

    if question.lower().startswith("llm "):
        actual_question = question[4:].strip()
        return DiscordJobCommand(question=actual_question, use_llm=True) if actual_question else None
    return DiscordJobCommand(question=question, use_llm=False)


def build_help_message(command_prefix: str = "!job", respond_to_all: bool = False) -> str:
    lines = [
        f"\ube60\ub978 \uac80\uc0c9: `{command_prefix} \ub300\uc804\uc5d0\uc11c 8-9\ub144\ucc28 AI \uacf5\uace0 \uc54c\ub824\uc918`",
        f"\uc0c1\uc138 \ubcf4\uae30: `{command_prefix} detail 1`",
        f"LLM \uc0c1\uc138 \ub2f5\ubcc0: `{command_prefix} llm \ub300\uc804\uc5d0\uc11c 8-9\ub144\ucc28 AI \uacf5\uace0 \uc54c\ub824\uc918`",
    ]
    if respond_to_all:
        lines.extend(
            [
                "\uc77c\ubc18 \uba54\uc2dc\uc9c0 \ube60\ub978 \uac80\uc0c9: `\ub300\uc804\uc5d0\uc11c 8-9\ub144\ucc28 AI \uacf5\uace0 \uc54c\ub824\uc918`",
                "\uc77c\ubc18 \uba54\uc2dc\uc9c0 \uc0c1\uc138 \ubcf4\uae30: `detail 1`",
                "\uc77c\ubc18 \uba54\uc2dc\uc9c0 LLM \uc0c1\uc138 \ub2f5\ubcc0: `llm \ub300\uc804\uc5d0\uc11c 8-9\ub144\ucc28 AI \uacf5\uace0 \uc54c\ub824\uc918`",
            ]
        )
    return "\n".join(lines)


def split_discord_message(message: str, limit: int = 1900) -> list[str]:
    if len(message) <= limit:
        return [message]
    chunks = []
    remaining = message
    while remaining:
        chunks.append(remaining[:limit].rstrip())
        remaining = remaining[limit:]
    return chunks


def search_discord_job_candidates(question: str, config: DiscordBotConfig) -> list[JobSearchResult]:
    jobs = load_jobs(config.input_path)
    return search_jobs(question, jobs, limit=config.limit)


def format_discord_job_candidates(results: list[JobSearchResult], include_llm_notice: bool = False) -> str:
    message = format_search_summary_results(results)
    if include_llm_notice:
        return message + "\n\n\uc0c1\uc138 \ub2f5\ubcc0\uc744 \uc0dd\uc131 \uc911\uc785\ub2c8\ub2e4. \ub85c\uceec Ollama \uc0c1\ud0dc\uc5d0 \ub530\ub77c \uc2dc\uac04\uc774 \uac78\ub9b4 \uc218 \uc788\uc2b5\ub2c8\ub2e4."
    return message


def format_discord_job_detail(result: JobSearchResult, index: int) -> str:
    return format_search_detail_result(result, index=index)


def answer_discord_job_question(question: str, config: DiscordBotConfig) -> str:
    return answer_job_question(
        question,
        input_path=config.input_path,
        limit=config.limit,
        model=config.model,
    )


def answer_discord_job_question_from_results(
    question: str,
    results: list[JobSearchResult],
    config: DiscordBotConfig,
) -> str:
    return answer_question_with_ollama(question, results, model=config.model)


def _parse_detail_index(question: str) -> int | None:
    parts = question.strip().split()
    if len(parts) != 2:
        return None
    command, raw_index = parts
    if command.lower() not in {"detail", "details", "\uc0c1\uc138"}:
        return None
    try:
        index = int(raw_index)
    except ValueError:
        return None
    return index if index > 0 else None


def _read_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}
