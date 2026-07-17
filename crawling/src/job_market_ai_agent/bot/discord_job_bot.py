from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from job_market_ai_agent.notifications.env import load_env_file
from job_market_ai_agent.qa.service import DEFAULT_JOBS_INPUT, answer_job_question


@dataclass(frozen=True)
class DiscordBotConfig:
    token: str
    command_prefix: str = "!job"
    input_path: Path = Path(DEFAULT_JOBS_INPUT)
    limit: int = 5
    model: str = "qwen2.5:3b"


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
        limit=int(os.getenv("JOB_QA_LIMIT", "5")),
        model=os.getenv("JOB_QA_MODEL", "qwen2.5:3b"),
    )


def extract_job_question(content: str, command_prefix: str = "!job") -> str | None:
    stripped = content.strip()
    if not stripped.startswith(command_prefix):
        return None
    question = stripped[len(command_prefix) :].strip()
    return question or None


def build_help_message(command_prefix: str = "!job") -> str:
    return f"사용법: `{command_prefix} 대전에서 8-9년차 AI 공고 알려줘`"


def split_discord_message(message: str, limit: int = 1900) -> list[str]:
    if len(message) <= limit:
        return [message]
    chunks = []
    remaining = message
    while remaining:
        chunks.append(remaining[:limit].rstrip())
        remaining = remaining[limit:]
    return chunks


def answer_discord_job_question(question: str, config: DiscordBotConfig) -> str:
    return answer_job_question(
        question,
        input_path=config.input_path,
        limit=config.limit,
        model=config.model,
    )
