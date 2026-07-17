from __future__ import annotations

from dataclasses import dataclass, field


REGION_ALIASES = {
    "대전": ["대전", "daejeon"],
    "세종": ["세종", "sejong"],
    "서울": ["서울", "seoul"],
}

TECH_KEYWORDS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "nextjs",
    "sql",
    "aws",
    "docker",
    "kubernetes",
    "ai",
    "llm",
    "rag",
]

ROLE_KEYWORDS = {
    "backend": ["backend", "백엔드", "서버"],
    "frontend": ["frontend", "프론트", "react", "next.js", "nextjs"],
    "ai": ["ai", "인공지능", "llm", "rag", "머신러닝", "ml"],
    "data": ["data", "데이터", "sql"],
}


@dataclass(frozen=True)
class QueryIntent:
    raw_query: str
    terms: list[str]
    regions: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    role_terms: list[str] = field(default_factory=list)
    deadline_types: list[str] = field(default_factory=list)
    experienced: bool = False
    require_analyzed: bool = False


def parse_query_intent(query: str) -> QueryIntent:
    normalized = _normalize(query)
    terms = _query_terms(normalized)
    regions = [region for region, aliases in REGION_ALIASES.items() if any(alias in normalized for alias in aliases)]
    skills = [skill for skill in TECH_KEYWORDS if skill in normalized]
    role_terms = [role for role, aliases in ROLE_KEYWORDS.items() if any(alias in normalized for alias in aliases)]
    deadline_types = _extract_deadline_types(normalized)
    experienced = any(token in normalized for token in ["8년", "9년", "8-9", "8~9", "시니어", "경력"])
    require_analyzed = experienced or "적합" in normalized or "추천" in normalized
    return QueryIntent(
        raw_query=query,
        terms=terms,
        regions=regions,
        skills=skills,
        role_terms=role_terms,
        deadline_types=deadline_types,
        experienced=experienced,
        require_analyzed=require_analyzed,
    )


def classify_deadline_text(deadline_text: str | None, deadline: str | None = None) -> str:
    combined = f"{deadline_text or ''} {deadline or ''}".replace(" ", "").lower()
    if not combined:
        return "unknown"
    if "채용시" in combined or "채용완료시" in combined:
        return "until_hired"
    if "상시" in combined:
        return "always_open"
    if combined.startswith("d-") or "d-" in combined or deadline:
        return "fixed_deadline"
    return "other"


def _extract_deadline_types(normalized: str) -> list[str]:
    deadline_types = []
    if "채용시" in normalized or "채용 시" in normalized:
        deadline_types.append("until_hired")
    if "상시" in normalized:
        deadline_types.append("always_open")
    if "d-" in normalized or "마감" in normalized or "날짜" in normalized:
        deadline_types.append("fixed_deadline")
    return deadline_types


def _query_terms(normalized: str) -> list[str]:
    raw_terms = [term.strip() for term in normalized.replace("/", " ").replace(",", " ").split()]
    return [term for term in raw_terms if len(term) >= 2]


def _normalize(query: str) -> str:
    return query.lower().replace("·", " ").replace("ㆍ", " ")
