from pathlib import Path

from job_market_ai_agent.storage.latest import default_latest_path, update_latest_json


def test_default_latest_path_uses_output_dir() -> None:
    assert default_latest_path(Path("data/raw/saramin")) == Path("data/raw/saramin/latest.json")


def test_update_latest_json_copies_source(tmp_path) -> None:
    source = tmp_path / "2026-07-18_AI.json"
    latest = tmp_path / "nested" / "latest.json"
    source.write_text('[{"title":"AI Engineer"}]', encoding="utf-8")

    result = update_latest_json(source, latest)

    assert result == latest
    assert latest.read_text(encoding="utf-8") == '[{"title":"AI Engineer"}]'
