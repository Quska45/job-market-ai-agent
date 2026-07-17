from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup, Tag

from job_market_ai_agent.collectors.base import JobCollector
from job_market_ai_agent.core.hashing import build_content_hash
from job_market_ai_agent.core.models import (
    CompanyInfo,
    CrawlMetadata,
    EmploymentInfo,
    JobInfo,
    JobPosting,
    LocationInfo,
    PostingContent,
    PostingDates,
)
from job_market_ai_agent.core.text import clean_text, unique_preserving_order


SARAMIN_BASE_URL = "https://www.saramin.co.kr"
DEFAULT_SEARCH_URL = "https://www.saramin.co.kr/zf_user/search/recruit"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)


@dataclass(frozen=True)
class SaraminListItem:
    source_job_id: str
    url: str
    title: str
    company_name: str
    company_url: str | None = None
    location_summary: str | None = None
    experience: str | None = None
    education: str | None = None
    deadline_text: str | None = None
    job_sectors: list[str] | None = None
    list_page: int | None = None


@dataclass(frozen=True)
class SaraminDetail:
    title: str | None = None
    company_name: str | None = None
    company_url: str | None = None
    location_summary: str | None = None
    address: str | None = None
    sub_categories: list[str] | None = None
    position: str | None = None
    skills: list[str] | None = None
    employment_type: str | None = None
    experience: str | None = None
    education: str | None = None
    posted_at: str | None = None
    deadline: str | None = None
    deadline_text: str | None = None
    company_size_type: str | None = None
    employee_count: str | None = None
    description: str | None = None
    raw_text: str | None = None
    image_urls: list[str] | None = None


class SaraminCollector(JobCollector):
    def __init__(
        self,
        keyword: str,
        max_jobs: int = 20,
        max_pages: int = 1,
        delay_seconds: float = 1.0,
        search_url: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.keyword = keyword
        self.max_jobs = max_jobs
        self.max_pages = max_pages
        self.delay_seconds = delay_seconds
        self.search_url = search_url or DEFAULT_SEARCH_URL
        self.client = httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            },
        )

    def build_search_url(self, page: int) -> str:
        parsed = urlparse(self.search_url)
        query = parse_qs(parsed.query)
        query.setdefault("searchType", ["search"])
        query["searchword"] = [self.keyword]
        query["recruitPage"] = [str(page)]
        encoded_query = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=encoded_query))

    def collect(self) -> list[JobPosting]:
        postings: list[JobPosting] = []
        seen_urls: set[str] = set()

        for page in range(1, self.max_pages + 1):
            list_html = self._get_text(self.build_search_url(page))
            items = parse_saramin_list(list_html, list_page=page)

            for item in items:
                if len(postings) >= self.max_jobs:
                    return postings
                if item.url in seen_urls:
                    continue
                seen_urls.add(item.url)

                try:
                    detail_html = self._get_detail_text(item)
                    detail = parse_saramin_detail(detail_html)
                except httpx.HTTPError:
                    detail = SaraminDetail()

                postings.append(build_job_posting(item, detail))
                time.sleep(self.delay_seconds)

            time.sleep(self.delay_seconds)

        return postings


    def _get_detail_text(self, item: SaraminListItem) -> str:
        ajax_url = urljoin(SARAMIN_BASE_URL, "/zf_user/jobs/relay/view-ajax")
        response = self.client.get(
            ajax_url,
            params={"rec_idx": item.source_job_id, "view_type": "list"},
            headers={"Referer": item.url},
        )
        response.raise_for_status()
        if "wrap_jv_cont" in response.text or "jv_cont" in response.text:
            return response.text
        return self._get_text(item.url)
    def close(self) -> None:
        self.client.close()

    def _get_text(self, url: str) -> str:
        response = self.client.get(url)
        response.raise_for_status()
        return response.text


def parse_saramin_list(html: str, list_page: int | None = None) -> list[SaraminListItem]:
    soup = BeautifulSoup(html, "html.parser")
    default_list = soup.select_one("#default_list_wrap")
    if default_list is not None:
        return _parse_default_list_wrap(default_list, list_page)

    items: list[SaraminListItem] = []
    seen_ids: set[str] = set()

    for link in soup.select('a[href*="/zf_user/jobs/relay/view"]'):
        href = link.get("href")
        if not href:
            continue
        absolute_url = urljoin(SARAMIN_BASE_URL, href)
        source_job_id = _extract_rec_idx(absolute_url)
        if not source_job_id or source_job_id in seen_ids:
            continue
        seen_ids.add(source_job_id)

        container = _find_job_container(link)
        title = clean_text(link.get_text(" ", strip=True))
        company_link = _select_first(container, [".corp_name a", ".area_corp a", 'a[href*="company"]'])
        company_name = clean_text(company_link.get_text(" ", strip=True) if company_link else "")
        company_url = _absolute_href(company_link)

        condition_texts = _texts_from_selectors(
            container,
            [".job_condition span", ".job_condition", ".condition span", ".recruit_condition span"],
        )

        deadline = _first_text(
            _texts_from_selectors(container, [".support_info .date", ".date", ".deadlines"])
        )

        items.append(
            SaraminListItem(
                source_job_id=source_job_id,
                url=absolute_url,
                title=title,
                company_name=company_name or "Unknown",
                company_url=company_url,
                location_summary=_first_matching(condition_texts, ("서울", "경기", "인천", "부산", "대구")),
                experience=_first_matching(condition_texts, ("신입", "경력", "무관", "년")),
                education=_first_matching(condition_texts, ("학력", "졸", "고등", "전문")),
                deadline_text=deadline,
                list_page=list_page,
            )
        )

    return items




def _parse_default_list_wrap(root: Tag, list_page: int | None = None) -> list[SaraminListItem]:
    items: list[SaraminListItem] = []
    seen_ids: set[str] = set()

    for container in root.select(".list_item"):
        link = container.select_one('.job_tit a[href*="/zf_user/jobs/relay/view"]')
        if not isinstance(link, Tag):
            continue
        href = link.get("href")
        if not href:
            continue
        absolute_url = urljoin(SARAMIN_BASE_URL, href)
        source_job_id = _extract_rec_idx(absolute_url)
        if not source_job_id or source_job_id in seen_ids:
            continue
        seen_ids.add(source_job_id)

        company_link = container.select_one(".company_nm a.str_tit")
        company_name = clean_text(company_link.get_text(" ", strip=True) if company_link else "")
        company_url = _absolute_href(company_link if isinstance(company_link, Tag) else None)

        items.append(
            SaraminListItem(
                source_job_id=source_job_id,
                url=absolute_url,
                title=clean_text(link.get("title") or link.get_text(" ", strip=True)),
                company_name=company_name or "Unknown",
                company_url=company_url,
                location_summary=_text_or_none(container.select_one(".work_place")),
                experience=_text_or_none(container.select_one(".career")),
                education=_text_or_none(container.select_one(".education")),
                deadline_text=_text_or_none(container.select_one(".support_info .date")),
                job_sectors=_texts_from_selectors(container, [".job_sector span"]),
                list_page=list_page,
            )
        )

    return items

def parse_saramin_detail(html: str) -> SaraminDetail:
    soup = BeautifulSoup(html, "html.parser")
    label_values = _extract_label_values(soup)
    raw_text = _extract_meaningful_detail_text(soup)
    description = _clean_job_description(_extract_full_detail_text(soup) or _extract_combined_detail_text(soup) or raw_text)

    sub_categories = _texts_from_selectors(
        soup,
        [".job_sector span", ".job_sector a", '[class*="sector"] span', '[class*="직무"] span'],
    )
    skills = _texts_from_selectors(
        soup,
        [".job_skill span", ".job_skill a", '[class*="skill"] span', '[class*="stack"] span'],
    )
    if not skills:
        skills = _extract_known_skills(raw_text or "")

    company_link = _select_first(
        soup,
        [
            ".jv_header .company a",
            ".jv_company_name a",
            ".company_info .company a",
            ".wrap_jv_header .company a",
        ],
    )
    title = _first_text(_texts_from_selectors(soup, [".tit_job", "h1", ".job_tit"]))

    return SaraminDetail(
        title=title,
        company_name=clean_text(company_link.get_text(" ", strip=True) if company_link else ""),
        company_url=_absolute_href(company_link),
        location_summary=_value_for(label_values, "근무지역", "지역"),
        address=_value_for(label_values, "주소", "근무지주소"),
        sub_categories=unique_preserving_order(sub_categories),
        position=_value_for(label_values, "직무", "포지션"),
        skills=unique_preserving_order(skills),
        employment_type=_value_for(label_values, "고용형태", "근무형태"),
        experience=_value_for(label_values, "경력", "지원자격"),
        education=_value_for(label_values, "학력"),
        posted_at=_value_for(label_values, "시작일", "공고시작일", "접수시작일"),
        deadline=_value_for(label_values, "마감일", "공고마감일", "접수마감일"),
        deadline_text=_value_for(label_values, "접수기간", "남은기간"),
        company_size_type=_value_for(label_values, "기업형태", "기업규모"),
        employee_count=_value_for(label_values, "사원수", "직원수", "재직중인 사람수"),
        description=description,
        raw_text=raw_text,
        image_urls=_extract_detail_image_urls(soup),
    )


def build_job_posting(item: SaraminListItem, detail: SaraminDetail) -> JobPosting:
    content_hash_payload = {
        "source": "saramin",
        "source_job_id": item.source_job_id,
        "title": detail.title or item.title,
        "company": detail.company_name or item.company_name,
        "description": detail.description or detail.raw_text,
    }

    return JobPosting(
        source="saramin",
        source_job_id=item.source_job_id,
        url=item.url,
        title=detail.title or item.title,
        company=CompanyInfo(
            name=_choose_company_name(item.company_name, detail.company_name),
            url=item.company_url or detail.company_url,
            size_type=detail.company_size_type,
            employee_count=detail.employee_count,
        ),
        location=LocationInfo(
            summary=detail.location_summary or item.location_summary,
            address=detail.address,
            region_level1=_split_region(detail.location_summary or item.location_summary)[0],
            region_level2=_split_region(detail.location_summary or item.location_summary)[1],
        ),
        job=JobInfo(
            category="IT",
            sub_categories=detail.sub_categories or item.job_sectors or [],
            position=detail.position,
        ),
        skills=detail.skills or [],
        employment=EmploymentInfo(
            type=detail.employment_type,
            experience=detail.experience or item.experience,
            education=detail.education or item.education,
        ),
        dates=PostingDates(
            posted_at=detail.posted_at,
            deadline=detail.deadline,
            deadline_text=detail.deadline_text or item.deadline_text,
        ),
        content=PostingContent(
            description=detail.description or _build_list_description(item),
            raw_text=detail.raw_text,
            image_urls=detail.image_urls or [],
        ),
        crawl=CrawlMetadata(
            collected_at=datetime.now().astimezone(),
            content_hash=build_content_hash(content_hash_payload),
            list_page=item.list_page,
        ),
    )


def _find_job_container(link: Tag) -> Tag:
    for parent in link.parents:
        if not isinstance(parent, Tag):
            continue
        class_text = " ".join(parent.get("class", []))
        if any(token in class_text for token in ("item_recruit", "list_item", "job_item", "recruit")):
            return parent
    return link.parent if isinstance(link.parent, Tag) else link


def _extract_rec_idx(url: str) -> str | None:
    query = parse_qs(urlparse(url).query)
    rec_idx = query.get("rec_idx")
    if rec_idx and rec_idx[0]:
        return rec_idx[0]
    match = re.search(r"rec_idx=(\d+)", url)
    return match.group(1) if match else None


def _absolute_href(tag: Tag | None) -> str | None:
    if tag is None:
        return None
    href = tag.get("href")
    if not href:
        return None
    return urljoin(SARAMIN_BASE_URL, href)




def _text_or_none(tag: Tag | None) -> str | None:
    if tag is None:
        return None
    text = clean_text(tag.get_text(" ", strip=True))
    return text or None

def _select_first(root: Tag | BeautifulSoup, selectors: Iterable[str]) -> Tag | None:
    for selector in selectors:
        selected = root.select_one(selector)
        if isinstance(selected, Tag):
            return selected
    return None


def _texts_from_selectors(root: Tag | BeautifulSoup, selectors: Iterable[str]) -> list[str]:
    texts: list[str] = []
    for selector in selectors:
        for tag in root.select(selector):
            text = clean_text(tag.get_text(" ", strip=True))
            if text:
                texts.append(text)
    return unique_preserving_order(texts)


def _first_text(values: list[str]) -> str | None:
    return values[0] if values else None


def _first_matching(values: list[str], needles: tuple[str, ...]) -> str | None:
    for value in values:
        if any(needle in value for needle in needles):
            return value
    return None


def _extract_label_values(soup: BeautifulSoup) -> dict[str, str]:
    values: dict[str, str] = {}

    for dt in soup.find_all("dt"):
        if not isinstance(dt, Tag):
            continue
        dd = dt.find_next_sibling("dd")
        if not isinstance(dd, Tag):
            continue
        label = clean_text(dt.get_text(" ", strip=True)).rstrip(":")
        value = clean_text(dd.get_text(" ", strip=True))
        if label and value:
            values[label] = value

    for row in soup.select("tr"):
        cells = [clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
        if len(cells) >= 2 and cells[0] and cells[1]:
            values[cells[0].rstrip(":")] = cells[1]

    return values


def _value_for(values: dict[str, str], *labels: str) -> str | None:
    for label in labels:
        if label in values:
            return values[label]
    for key, value in values.items():
        if any(label in key for label in labels):
            return value
    return None


def _extract_known_skills(text: str) -> list[str]:
    known_skills = [
        "Python",
        "Java",
        "JavaScript",
        "TypeScript",
        "React",
        "Vue",
        "Node.js",
        "Spring",
        "FastAPI",
        "Django",
        "AWS",
        "Docker",
        "Kubernetes",
        "SQL",
        "PostgreSQL",
        "MySQL",
        "PyTorch",
        "TensorFlow",
        "LLM",
        "RAG",
        "LangChain",
        "LangGraph",
    ]
    return [skill for skill in known_skills if re.search(rf"(?<![A-Za-z]){re.escape(skill)}(?![A-Za-z])", text)]










NOISE_PHRASES = [
    "기업리뷰",
    "면접후기",
    "복리후생",
    "조회수",
    "공유하기",
    "페이스북",
    "트위터",
    "URL복사",
    "SMS발송",
    "신고하기",
    "최저임금계산에 대한 알림",
    "하단에 명시된 급여, 근무 내용 등이 최저임금에 미달하는 경우 위 내용이 우선합니다.",
    "지도보기",
    "지도 보기",
    "지도초기화",
    "스카이뷰",
    "크게보기",
    "길찾기",
    "닫기",
    "상세보기",
    "관심기업",
    "입사지원",
    "채용중",
    "이 기업의 다른 공고",
    "스크랩",
    "지원 TOP100",
    "스크랩 TOP100",
    "조회 TOP100",
    "급상승",
]


def _clean_job_description(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = text
    for phrase in NOISE_PHRASES:
        cleaned = cleaned.replace(phrase, " ")
    cleaned = re.sub(r"남은 기간\s+00\s+일\s+00:00:00", " ", cleaned)
    cleaned = re.sub(r"\bTOP\b", " ", cleaned)
    cleaned = clean_text(cleaned)
    return cleaned or None
def _extract_full_detail_text(soup: BeautifulSoup) -> str | None:
    root = soup.select_one(".wrap_jv_cont") or soup.select_one(".jv_cont")
    if root is None:
        return None
    for tag in root.select("script, style, noscript"):
        tag.decompose()
    text = clean_text(root.get_text(" ", strip=True))
    return text if len(text) >= 80 else None


def _extract_detail_image_urls(soup: BeautifulSoup) -> list[str]:
    root = soup.select_one(".wrap_jv_cont") or soup.select_one(".jv_cont") or soup
    urls: list[str] = []
    for image in root.select("img"):
        src = image.get("src") or image.get("data-src")
        if not src:
            continue
        absolute_url = urljoin(SARAMIN_BASE_URL, src)
        alt = clean_text(image.get("alt"))
        urls.append(f"{alt} | {absolute_url}" if alt else absolute_url)
    return unique_preserving_order(urls)
def _extract_combined_detail_text(soup: BeautifulSoup) -> str | None:
    sections = [
        ".jv_cont",
        ".jv_howto",
        ".jv_company",
        ".jv_location",
        ".user_content",
        ".job_description",
        ".cont_recruit",
    ]
    texts: list[str] = []
    for selector in sections:
        node = soup.select_one(selector)
        if node is None:
            continue
        text = clean_text(node.get_text(" ", strip=True))
        if len(text) >= 20:
            texts.append(text)
    combined = clean_text("\n".join(unique_preserving_order(texts)))
    return combined or None
def _extract_meaningful_detail_text(soup: BeautifulSoup) -> str | None:
    selectors = [
        ".jv_cont",
        ".jv_summary",
        ".user_content",
        ".job_description",
        ".cont_recruit",
        ".jv_detail",
        ".wrap_jv_body",
        "#iframe_content_0",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if node is None:
            continue
        text = clean_text(node.get_text(" ", strip=True))
        if len(text) >= 80:
            return text
    return None


def _build_list_description(item: SaraminListItem) -> str:
    parts = [
        item.title,
        item.company_name,
        item.location_summary,
        item.experience,
        item.education,
        ", ".join(item.job_sectors or []),
        item.deadline_text,
    ]
    return clean_text(" | ".join(part for part in parts if part))
def _split_region(summary: str | None) -> tuple[str | None, str | None]:
    if not summary:
        return None, None
    parts = summary.split()
    if not parts:
        return None, None
    return parts[0], parts[1] if len(parts) > 1 else None



def _choose_company_name(list_company: str, detail_company: str | None) -> str:
    blocked_detail_values = {"기업큐레이션", "기업정보", "기업·연봉"}
    if detail_company and detail_company not in blocked_detail_values:
        return detail_company
    return list_company














