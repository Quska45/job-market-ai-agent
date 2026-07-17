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
    load_discord_bot_config,
    parse_job_command,
    split_discord_message,
)
from job_market_ai_agent.qa.search import JobSearchResult


def test_extract_job_question() -> None:
    assert extract_job_question("!job 대전 AI 공고") == "대전 AI 공고"
    assert extract_job_question("!job") is None
    assert extract_job_question("hello") is None


def test_parse_job_command_defaults_to_fast_search() -> None:
    command = parse_job_command("!job 대전 AI 공고")

    assert command is not None
    assert command.question == "대전 AI 공고"
    assert command.use_llm is False


def test_parse_job_command_supports_llm_mode() -> None:
    command = parse_job_command("!job llm 대전 AI 공고")

    assert command is not None
    assert command.question == "대전 AI 공고"
    assert command.use_llm is True


def test_build_help_message_mentions_modes() -> None:
    message = build_help_message("!job")

    assert "!job" in message
    assert "!job llm" in message


def test_split_discord_message_chunks_long_text() -> None:
    chunks = split_discord_message("A" * 25, limit=10)

    assert chunks == ["AAAAAAAAAA", "AAAAAAAAAA", "AAAAA"]


def test_load_discord_bot_config_reads_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "DISCORD_BOT_TOKEN=test-token\n"
        "DISCORD_BOT_COMMAND_PREFIX=!채용\n"
        "JOB_QA_INPUT=data/raw/jobs.json\n"
        "JOB_QA_LIMIT=3\n"
        "JOB_QA_MODEL=qwen2.5:3b\n",
        encoding="utf-8",
    )

    config = load_discord_bot_config(env_path)

    assert config.token == "test-token"
    assert config.command_prefix == "!채용"
    assert config.input_path == Path("data/raw/jobs.json")
    assert config.limit == 3


def test_load_discord_bot_config_requires_token(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)

    with pytest.raises(DiscordBotConfigurationError):
        load_discord_bot_config(tmp_path / ".env")


def test_format_discord_job_candidates_fast_mode_points_to_llm_command() -> None:
    result = JobSearchResult(
        job={"title": "AI Engineer", "company": {"name": "Example"}, "dates": {}, "url": "u"},
        score=3,
        matched_terms=["ai"],
    )

    output = format_discord_job_candidates([result])

    assert "검색 후보" in output
    assert "!job llm" in output
    assert "상세 답변을 생성 중" not in output


def test_format_discord_job_candidates_llm_mode_adds_progress_message() -> None:
    result = JobSearchResult(
        job={"title": "AI Engineer", "company": {"name": "Example"}, "dates": {}, "url": "u"},
        score=3,
        matched_terms=["ai"],
    )

    output = format_discord_job_candidates([result], include_llm_notice=True)

    assert "검색 후보" in output
    assert "상세 답변을 생성 중" in output


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

    assert answer_discord_job_question("질문", config) == "answer"
    assert calls == [("질문", Path("jobs.json"), 2, "model")]


def test_answer_discord_job_question_from_results_delegates(monkeypatch) -> None:
    calls = []

    def fake_answer(question, results, model):
        calls.append((question, results, model))
        return "answer"

    monkeypatch.setattr("job_market_ai_agent.bot.discord_job_bot.answer_question_with_ollama", fake_answer)
    results = [JobSearchResult(job={}, score=1, matched_terms=[])]
    config = DiscordBotConfig(token="token", model="model")

    assert answer_discord_job_question_from_results("질문", results, config) == "answer"
    assert calls == [("질문", results, "model")]
