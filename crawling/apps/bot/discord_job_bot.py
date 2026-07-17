from __future__ import annotations

import asyncio
import sys
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


def main() -> None:
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
        print(f"discord_job_bot_ready: {client.user}")

    @client.event
    async def on_message(message) -> None:
        if message.author == client.user or message.author.bot:
            return
        command = parse_job_command(message.content, config.command_prefix)
        if command is None:
            return
        if command.question in {"help", "도움말"}:
            await message.channel.send(build_help_message(config.command_prefix))
            return

        try:
            results = await asyncio.to_thread(search_discord_job_candidates, command.question, config)
            for chunk in split_discord_message(
                format_discord_job_candidates(results, include_llm_notice=command.use_llm)
            ):
                await message.channel.send(chunk)
            if not command.use_llm:
                return
            async with message.channel.typing():
                response = await asyncio.to_thread(
                    answer_discord_job_question_from_results,
                    command.question,
                    results,
                    config,
                )
            for chunk in split_discord_message(response):
                await message.channel.send(chunk)
        except Exception as error:
            await message.channel.send(
                "요청 처리 중 오류가 발생했습니다. "
                f"검색 후보를 먼저 확인해 주세요. 오류: {error}"
            )

    client.run(config.token)


if __name__ == "__main__":
    main()
