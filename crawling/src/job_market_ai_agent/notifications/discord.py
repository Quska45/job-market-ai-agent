from __future__ import annotations

import os
from typing import Any

import httpx


class NotificationError(RuntimeError):
    pass


def send_discord_notification(message: str, webhook_url: str | None = None) -> bool:
    url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        return False

    response = httpx.post(url, json={"content": _limit_message(message)}, timeout=30)
    if response.status_code >= 400:
        raise NotificationError(f"Discord webhook error {response.status_code}: {response.text[:300]}")
    return True


def notify(message: str, channels: list[str]) -> list[str]:
    sent_channels: list[str] = []
    for channel in channels:
        if channel == "console":
            print(message)
            sent_channels.append(channel)
        elif channel == "discord":
            if send_discord_notification(message):
                sent_channels.append(channel)
        else:
            raise NotificationError(f"Unsupported notification channel: {channel}")
    return sent_channels


def _limit_message(message: str) -> str:
    if len(message) <= 1900:
        return message
    return message[:1900].rstrip() + "\n..."
