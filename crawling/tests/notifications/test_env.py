import os

from job_market_ai_agent.notifications.env import load_env_file


def test_load_env_file_sets_missing_values(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("DISCORD_WEBHOOK_URL=https://example.com\n", encoding="utf-8")

    load_env_file(env_path)

    assert os.environ["DISCORD_WEBHOOK_URL"] == "https://example.com"
