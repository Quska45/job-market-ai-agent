from pathlib import Path

from job_market_ai_agent.collectors.saramin import SaraminCollector, parse_saramin_detail, parse_saramin_list


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_parse_saramin_list_extracts_job_cards() -> None:
    html = (FIXTURE_DIR / "saramin_list.html").read_text(encoding="utf-8")

    items = parse_saramin_list(html)

    assert len(items) == 1
    assert items[0].source_job_id == "501"
    assert items[0].title == "AI 플랫폼 개발자"
    assert items[0].company_name == "테스트랩"
    assert items[0].location_summary == "서울 강남구"
    assert items[0].deadline_text == "~08.31(토)"


def test_parse_saramin_detail_extracts_required_fields() -> None:
    html = (FIXTURE_DIR / "saramin_detail.html").read_text(encoding="utf-8")

    detail = parse_saramin_detail(html)

    assert detail.address == "서울 강남구 테헤란로 123"
    assert detail.sub_categories == ["백엔드", "AI/ML"]
    assert detail.skills == ["Python", "FastAPI", "RAG"]
    assert detail.company_size_type == "중소기업"
    assert detail.employee_count == "42명"
    assert detail.posted_at == "2026.07.17"
    assert detail.deadline == "2026.08.31"


def test_build_search_url_supports_keyword_and_page() -> None:
    collector = SaraminCollector(keyword="AI", max_jobs=10)

    url = str(collector.build_search_url(page=2))

    assert "searchword=AI" in url
    assert "recruitPage=2" in url



def test_build_job_posting_prefers_list_company_over_detail_navigation_link() -> None:
    from job_market_ai_agent.collectors.saramin import SaraminDetail, SaraminListItem, build_job_posting

    item = SaraminListItem(
        source_job_id="501",
        url="https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=501",
        title="AI 플랫폼 개발자",
        company_name="테스트랩",
    )
    detail = SaraminDetail(company_name="기업큐레이션")

    posting = build_job_posting(item, detail)

    assert posting.company.name == "테스트랩"


def test_parse_saramin_job_category_list_extracts_default_list_items() -> None:
    html = (FIXTURE_DIR / "saramin_job_category_list.html").read_text(encoding="utf-8")

    items = parse_saramin_list(html)

    assert len(items) == 1
    assert items[0].source_job_id == "54217541"
    assert items[0].title == "AI 백엔드 개발자"
    assert items[0].company_name == "테스트랩"
    assert items[0].location_summary == "대전전체 외"
    assert items[0].experience == "신입 · 경력 · 정규직"
    assert items[0].education == "학력무관"
    assert items[0].deadline_text == "D-6"
