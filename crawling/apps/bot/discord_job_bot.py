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
    format_discord_job_detail,
    load_discord_bot_config,
    parse_job_command,
    search_discord_job_candidates,
    split_discord_message,
)
from job_market_ai_agent.qa.search import JobSearchResult  # noqa: E402


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


def _channel_key(message) -> int:
    return int(getattr(message.channel, "id", 0))


def _format_missing_detail_message() -> str:
    return "\uc9c1\uc804 \uac80\uc0c9 \uacb0\uacfc\uac00 \uc5c6\uc2b5\ub2c8\ub2e4. \uba3c\uc800 `\ub300\uc804 AI\uacf5\uace0`\ucc98\ub7fc \uac80\uc0c9\ud574 \uc8fc\uc138\uc694."


def _format_invalid_detail_message(index: int, results: list[JobSearchResult]) -> str:
    return f"{index}\ubc88 \uacf5\uace0\ub294 \uc5c6\uc2b5\ub2c8\ub2e4. \ud604\uc7ac \uc0c1\uc138 \ubcf4\uae30\ub294 1~{len(results)}\ubc88\uae4c\uc9c0 \uac00\ub2a5\ud569\ub2c8\ub2e4."


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

    recent_results_by_channel: dict[int, list[JobSearchResult]] = {}

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        _log(
            "discord_job_bot_ready: "
            f"user={client.user} prefix={config.command_prefix!r} "
            f"respond_to_all={config.respond_to_all} "
            f"input={config.input_path} limit={config.limit} model={config.model} "
            f"log={LOG_FILE}"
        )

    @client.event
    async def on_message(message) -> None:
        if message.author == client.user or message.author.bot:
            return
        command = parse_job_command(
            message.content,
            config.command_prefix,
            respond_to_all=config.respond_to_all,
        )
        if command is None:
            return
        started_at = time.perf_counter()
        channel_key = _channel_key(message)
        _log(
            "job_command_received: "
            f"channel={channel_key} use_llm={command.use_llm} "
            f"detail_index={command.detail_index} question={command.question!r}"
        )
        if command.question in {"help", "\ub3c4\uc6c0\ub9d0"}:
            await message.channel.send(build_help_message(config.command_prefix, config.respond_to_all))
            _log(f"job_help_sent: elapsed={_elapsed(started_at)}")
            return

        try:
            if command.detail_index is not None:
                results = recent_results_by_channel.get(channel_key, [])
                if not results:
                    await message.channel.send(_format_missing_detail_message())
                    _log(f"job_detail_missing_recent_results: elapsed={_elapsed(started_at)}")
                    return
                if command.detail_index > len(results):
                    await message.channel.send(_format_invalid_detail_message(command.detail_index, results))
                    _log(f"job_detail_invalid_index: index={command.detail_index} count={len(results)}")
                    return
                detail = format_discord_job_detail(results[command.detail_index - 1], command.detail_index)
                for chunk in split_discord_message(detail):
                    await message.channel.send(chunk)
                _log(f"job_detail_sent: index={command.detail_index} elapsed={_elapsed(started_at)}")
                return

            _log(f"job_search_started: input={config.input_path}")
            results = await asyncio.to_thread(search_discord_job_candidates, command.question, config)
            recent_results_by_channel[channel_key] = results
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
                "job_command_error: use_llm=%s detail_index=%s question=%r elapsed=%s",
                command.use_llm,
                command.detail_index,
                command.question,
                _elapsed(started_at),
            )
            await message.channel.send(
                "\uc694\uccad \ucc98\ub9ac \uc911 \uc624\ub958\uac00 \ubc1c\uc0dd\ud588\uc2b5\ub2c8\ub2e4. "
                f"\uac80\uc0c9 \ud6c4\ubcf4\ub97c \uba3c\uc800 \ud655\uc778\ud574 \uc8fc\uc138\uc694. \uc624\ub958: {error}"
            )

    client.run(config.token)


if __name__ == "__main__":
    main()
