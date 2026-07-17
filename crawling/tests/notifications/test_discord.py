from job_market_ai_agent.notifications.discord import notify, send_discord_notification


class DummyResponse:
    status_code = 204
    text = ""


def test_send_discord_notification_returns_false_without_url(monkeypatch) -> None:
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)

    assert send_discord_notification("hello") is False


def test_send_discord_notification_posts_content(monkeypatch) -> None:
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))
        return DummyResponse()

    monkeypatch.setattr("job_market_ai_agent.notifications.discord.httpx.post", fake_post)

    assert send_discord_notification("hello", webhook_url="https://discord.example/webhook") is True
    assert calls == [("https://discord.example/webhook", {"content": "hello"}, 30)]


def test_notify_console(capsys) -> None:
    sent = notify("hello", ["console"])

    assert sent == ["console"]
    assert "hello" in capsys.readouterr().out
