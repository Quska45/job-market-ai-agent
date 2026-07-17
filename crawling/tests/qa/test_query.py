from job_market_ai_agent.qa.query import classify_deadline_text, parse_query_intent


def test_parse_query_intent_extracts_regions_skills_roles_and_experience() -> None:
    intent = parse_query_intent("대전에서 8-9년차 Python 백엔드 AI 공고 알려줘")

    assert intent.regions == ["대전"]
    assert "python" in intent.skills
    assert "ai" in intent.skills
    assert "backend" in intent.role_terms
    assert intent.experienced is True
    assert intent.require_analyzed is True


def test_parse_query_intent_extracts_deadline_types() -> None:
    assert parse_query_intent("채용시 마감 공고").deadline_types == ["until_hired", "fixed_deadline"]
    assert parse_query_intent("상시 채용 공고").deadline_types == ["always_open"]


def test_classify_deadline_text() -> None:
    assert classify_deadline_text("채용시 마감") == "until_hired"
    assert classify_deadline_text("상시채용") == "always_open"
    assert classify_deadline_text("D-7") == "fixed_deadline"
    assert classify_deadline_text(None, "2026.08.01") == "fixed_deadline"
