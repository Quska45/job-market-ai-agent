from pathlib import Path

import pytest

from job_market_ai_agent.bot.discord_job_bot import (
    DiscordBotConfig,
    DiscordBotConfigurationError,
    answer_discord_job_question,
    answer_discord_job_question_from_results,
    build_help_message,
    extract_job_question,
    format_discord_job_candidates,
    format_discord_job_detail,
    load_discord_bot_config,
    parse_job_command,
    split_discord_message,
)
from job_market_ai_agent.qa.search import JobSearchResult


def _sample_result() -> JobSearchResult:
    return JobSearchResult(
        job={
            "title": "AI Engineer",
            "company": {"name": "Example", "size_type": "\uc911\uc18c\uae30\uc5c5"},
            "location": {"summary": "\ub300\uc804", "address": "\ub300\uc804 \uc720\uc131\uad6c"},
            "employment": {"experience": "\uacbd\ub825 5\ub144", "type": "\uc815\uaddc\uc9c1"},
            "dates": {"deadline_text": "D-7"},
            "skills": ["Python"],
            "analysis": {"fit_for_8_9_year_developer": 0.9, "main_tasks": ["AI \uac1c\ubc1c"]},
            "url": "u",
        },
        score=3,
        matched_terms=["ai"],
    )


def test_extract_job_question() -> None:
    assert extract_job_question("!job \ub300\uc804 AI \uacf5\uace0") == "\ub300\uc804 AI \uacf5\uace0"
    assert extract_job_question("!job") is None
    assert extract_job_question("hello") is None


def test_parse_job_command_defaults_to_fast_search() -> None:
    command = parse_job_command("!job \ub300\uc804 AI \uacf5\uace0")

    assert command is not None
    assert command.question == "\ub300\uc804 AI \uacf5\uace0"
    assert command.use_llm is False
    assert command.detail_index is None


def test_parse_job_command_supports_llm_mode() -> None:
    command = parse_job_command("!job llm \ub300\uc804 AI \uacf5\uace0")

    assert command is not None
    assert command.question == "\ub300\uc804 AI \uacf5\uace0"
    assert command.use_llm is True


def test_parse_job_command_supports_detail_mode() -> None:
    command = parse_job_command("!job detail 2")

    assert command is not None
    assert command.detail_index == 2
    assert command.question == ""


def test_parse_job_command_supports_korean_detail_mode() -> None:
    command = parse_job_command("\uc0c1\uc138 1", respond_to_all=True)

    assert command is not None
    assert command.detail_index == 1


def test_parse_job_command_supports_plain_message_when_enabled() -> None:
    command = parse_job_command("\ub300\uc804 AI \uacf5\uace0", respond_to_all=True)

    assert command is not None
    assert command.question == "\ub300\uc804 AI \uacf5\uace0"
    assert command.use_llm is False


def test_parse_job_command_supports_plain_llm_message_when_enabled() -> None:
    command = parse_job_command("llm \ub300\uc804 AI \uacf5\uace0", respond_to_all=True)

    assert command is not None
    assert command.question == "\ub300\uc804 AI \uacf5\uace0"
    assert command.use_llm is True


def test_parse_job_command_ignores_plain_message_by_default() -> None:
    assert parse_job_command("\ub300\uc804 AI \uacf5\uace0") is None


def test_build_help_message_mentions_modes() -> None:
    message = build_help_message("!job")

    assert "!job" in message
    assert "!job llm" in message
    assert "detail 1" in message


def test_build_help_message_mentions_plain_messages_when_enabled() -> None:
    message = build_help_message("!job", respond_to_all=True)

    assert "\uc77c\ubc18 \uba54\uc2dc\uc9c0 \ube60\ub978 \uac80\uc0c9" in message
    assert "detail 1" in message
    assert "llm \ub300\uc804" in message


def test_split_discord_message_chunks_long_text() -> None:
    chunks = split_discord_message("A" * 25, limit=10)

    assert chunks == ["AAAAAAAAAA", "AAAAAAAAAA", "AAAAA"]


def test_load_discord_bot_config_reads_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.delenv("DISCORD_BOT_RESPOND_TO_ALL", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "DISCORD_BOT_TOKEN=test-token\n"
        "DISCORD_BOT_COMMAND_PREFIX=!\uCC44\uC6A9\n"
        "DISCORD_BOT_RESPOND_TO_ALL=true\n"
        "JOB_QA_INPUT=data/raw/jobs.json\n"
        "JOB_QA_LIMIT=3\n"
        "JOB_QA_MODEL=qwen2.5:3b\n",
        encoding="utf-8",
    )

    config = load_discord_bot_config(env_path)

    assert config.token == "test-token"
    assert config.command_prefix == "!\uCC44\uC6A9"
    assert config.input_path == Path("data/raw/jobs.json")
    assert config.limit == 3
    assert config.respond_to_all is True


def test_load_discord_bot_config_requires_token(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)

    with pytest.raises(DiscordBotConfigurationError):
        load_discord_bot_config(tmp_path / ".env")


def test_format_discord_job_candidates_fast_mode_outputs_summary() -> None:
    output = format_discord_job_candidates([_sample_result()])

    assert "\uac80\uc0c9 \ud6c4\ubcf4 Top 3" in output
    assert "Example" in output
    assert "detail" in output
    assert "\uc8fc\uc18c:" not in output
    assert "\uc0c1\uc138 \ub2f5\ubcc0\uc744 \uc0dd\uc131 \uc911" not in output


def test_format_discord_job_candidates_llm_mode_adds_progress_message() -> None:
    output = format_discord_job_candidates([_sample_result()], include_llm_notice=True)

    assert "\uac80\uc0c9 \ud6c4\ubcf4 Top 3" in output
    assert "\uc0c1\uc138 \ub2f5\ubcc0\uc744 \uc0dd\uc131 \uc911" in output


def test_format_discord_job_detail_outputs_full_detail() -> None:
    output = format_discord_job_detail(_sample_result(), 1)

    assert "1. Example" in output
    assert "\uc8fc\uc18c:" in output
    assert "AI \uac1c\ubc1c" in output


def test_answer_discord_job_question_delegates(monkeypatch) -> None:
    calls = []

    def fake_answer(question, input_path, limit, model):
        calls.append((question, input_path, limit, model))
        return "answer"

    monkeypatch.setattr("job_market_ai_agent.bot.discord_job_bot.answer_job_question", fake_answer)
    config = DiscordBotConfig(
        token="token",
        input_path=Path("jobs.json"),
        limit=2,
        model="model",
    )

    assert answer_discord_job_question("\uc9c8\ubb38", config) == "answer"
    assert calls == [("\uc9c8\ubb38", Path("jobs.json"), 2, "model")]


def test_answer_discord_job_question_from_results_delegates(monkeypatch) -> None:
    calls = []

    def fake_answer(question, results, model):
        calls.append((question, results, model))
        return "answer"

    monkeypatch.setattr("job_market_ai_agent.bot.discord_job_bot.answer_question_with_ollama", fake_answer)
    results = [JobSearchResult(job={}, score=1, matched_terms=[])]
    config = DiscordBotConfig(token="token", model="model")

    assert answer_discord_job_question_from_results("\uc9c8\ubb38", results, config) == "answer"
    assert calls == [("\uc9c8\ubb38", results, "model")]
