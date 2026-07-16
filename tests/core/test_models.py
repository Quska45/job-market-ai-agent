from datetime import datetime

from job_market_ai_agent.core.models import CompanyInfo, CrawlMetadata, JobPosting


def test_job_posting_accepts_required_saramin_fields() -> None:
    posting = JobPosting(
        source="saramin",
        source_job_id="12345",
        url="https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=12345",
        title="AI Engineer",
        company=CompanyInfo(name="Example"),
        crawl=CrawlMetadata(
            collected_at=datetime.fromisoformat("2026-07-17T10:00:00+09:00"),
            content_hash="abc123",
        ),
    )

    assert posting.source == "saramin"
    assert posting.company.name == "Example"
    assert posting.location.address is None
    assert posting.company.employee_count is None

