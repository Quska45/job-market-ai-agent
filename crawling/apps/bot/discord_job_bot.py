from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))

from job_market_ai_agent.bot.discord_job_bot import (  # noqa: E402
    DiscordBotConfigurationError,
    answer_discord_job_question,
    build_help_message,
    extract_job_question,
    load_discord_bot_config,
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
        question = extract_job_question(message.content, config.command_prefix)
        if question is None:
            return
        async with message.channel.typing():
            if question in {"help", "도움말"}:
                response = build_help_message(config.command_prefix)
            else:
                response = await asyncio.to_thread(answer_discord_job_question, question, config)
        for chunk in split_discord_message(response):
            await message.channel.send(chunk)

    client.run(config.token)


if __name__ == "__main__":
    main()
