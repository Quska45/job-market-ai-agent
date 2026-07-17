from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from job_market_ai_agent.notifications.env import load_env_file
from job_market_ai_agent.qa.answer import answer_question_with_ollama, format_search_results
from job_market_ai_agent.qa.search import JobSearchResult, load_jobs, search_jobs
from job_market_ai_agent.qa.service import DEFAULT_JOBS_INPUT, answer_job_question


@dataclass(frozen=True)
class DiscordBotConfig:
    token: str
    command_prefix: str = "!job"
    input_path: Path = Path(DEFAULT_JOBS_INPUT)
    limit: int = 3
    model: str = "qwen2.5:3b"


@dataclass(frozen=True)
class DiscordJobCommand:
    question: str
    use_llm: bool = False


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
    )


def extract_job_question(content: str, command_prefix: str = "!job") -> str | None:
    command = parse_job_command(content, command_prefix)
    return command.question if command else None


def parse_job_command(content: str, command_prefix: str = "!job") -> DiscordJobCommand | None:
    stripped = content.strip()
    if not stripped.startswith(command_prefix):
        return None
    question = stripped[len(command_prefix) :].strip()
    if not question:
        return None
    if question.lower().startswith("llm "):
        actual_question = question[4:].strip()
        return DiscordJobCommand(question=actual_question, use_llm=True) if actual_question else None
    return DiscordJobCommand(question=question, use_llm=False)


def build_help_message(command_prefix: str = "!job") -> str:
    return "\n".join(
        [
            f"빠른 검색: `{command_prefix} 대전에서 8-9년차 AI 공고 알려줘`",
            f"LLM 상세 답변: `{command_prefix} llm 대전에서 8-9년차 AI 공고 알려줘`",
        ]
    )


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
    message = format_search_results(results)
    if include_llm_notice:
        return message + "\n\n상세 답변을 생성 중입니다. 로컬 Ollama 상태에 따라 시간이 걸릴 수 있습니다."
    return message + "\n\n상세 답변이 필요하면 `!job llm 질문`으로 다시 물어봐 주세요."


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
