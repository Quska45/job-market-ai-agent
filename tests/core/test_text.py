from job_market_ai_agent.core.text import clean_text


def test_clean_text_unescapes_and_removes_html_tags() -> None:
    assert clean_text("&lt;strong&gt;AI&lt;/strong&gt; 개발자") == "AI 개발자"
