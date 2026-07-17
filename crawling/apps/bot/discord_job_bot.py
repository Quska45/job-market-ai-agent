from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))

from job_market_ai_agent.bot.discord_job_bot import (  # noqa: E402
    DiscordBotConfigurationError,
    answer_discord_job_question_from_results,
    build_help_message,
    format_discord_job_candidates,
    load_discord_bot_config,
    parse_job_command,
    search_discord_job_candidates,
    split_discord_message,
)


LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "discord_job_bot.log"


def _setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


def _log(message: str) -> None:
    logging.info(message)


def _elapsed(started_at: float) -> str:
    return f"{time.perf_counter() - started_at:.2f}s"


def main() -> None:
    _setup_logging()
    try:
        import discord
    except ImportError as error:
        raise SystemExit("discord.py is required. Install it with: py -3 -m pip install discord.py") from error

    try:
        config = load_discord_bot_config(ROOT / ".env")
    except DiscordBotConfigurationError as error:
        raise SystemExit(str(error)) from error

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        _log(
            "discord_job_bot_ready: "
            f"user={client.user} prefix={config.command_prefix!r} "
            f"input={config.input_path} limit={config.limit} model={config.model} "
            f"log={LOG_FILE}"
        )

    @client.event
    async def on_message(message) -> None:
        if message.author == client.user or message.author.bot:
            return
        command = parse_job_command(message.content, config.command_prefix)
        if command is None:
            return
        started_at = time.perf_counter()
        _log(
            "job_command_received: "
            f"channel={getattr(message.channel, 'id', 'unknown')} "
            f"use_llm={command.use_llm} question={command.question!r}"
        )
        if command.question in {"help", "도움말"}:
            await message.channel.send(build_help_message(config.command_prefix))
            _log(f"job_help_sent: elapsed={_elapsed(started_at)}")
            return

        try:
            _log(f"job_search_started: input={config.input_path}")
            results = await asyncio.to_thread(search_discord_job_candidates, command.question, config)
            _log(f"job_candidates_found: count={len(results)} elapsed={_elapsed(started_at)}")
            for chunk in split_discord_message(
                format_discord_job_candidates(results, include_llm_notice=command.use_llm)
            ):
                await message.channel.send(chunk)
            _log(f"job_candidates_sent: elapsed={_elapsed(started_at)}")
            if not command.use_llm:
                _log(f"job_command_done_without_llm: elapsed={_elapsed(started_at)}")
                return
            _log(f"job_llm_started: model={config.model}")
            async with message.channel.typing():
                response = await asyncio.to_thread(
                    answer_discord_job_question_from_results,
                    command.question,
                    results,
                    config,
                )
            for chunk in split_discord_message(response):
                await message.channel.send(chunk)
            _log(f"job_llm_answer_sent: elapsed={_elapsed(started_at)}")
        except Exception as error:
            logging.exception(
                "job_command_error: use_llm=%s question=%r elapsed=%s",
                command.use_llm,
                command.question,
                _elapsed(started_at),
            )
            await message.channel.send(
                "요청 처리 중 오류가 발생했습니다. "
                f"검색 후보를 먼저 확인해 주세요. 오류: {error}"
            )

    client.run(config.token)


if __name__ == "__main__":
    main()
