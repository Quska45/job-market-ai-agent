from __future__ import annotations

from dataclasses import dataclass, field


REGION_ALIASES = {
    "\ub300\uc804": ["\ub300\uc804", "daejeon"],
    "\uc138\uc885": ["\uc138\uc885", "sejong"],
    "\uc11c\uc6b8": ["\uc11c\uc6b8", "seoul"],
}

TECH_KEYWORDS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "nextjs",
    "vue",
    "node",
    "spring",
    "sql",
    "aws",
    "docker",
    "kubernetes",
    "ai",
    "llm",
    "rag",
]

ROLE_KEYWORDS = {
    "backend": ["backend", "\ubc31\uc5d4\ub4dc", "\uc11c\ubc84", "spring", "api"],
    "frontend": ["frontend", "\ud504\ub860\ud2b8", "react", "next.js", "nextjs", "vue"],
    "fullstack": ["fullstack", "full-stack", "\ud480\uc2a4\ud0dd"],
    "ai": ["ai", "\uc778\uacf5\uc9c0\ub2a5", "llm", "rag", "\uba38\uc2e0\ub7ec\ub2dd", "ml"],
    "data": ["data", "\ub370\uc774\ud130", "sql", "etl", "\ub370\uc774\ud130\uc5d4\uc9c0\ub2c8\uc5b4"],
    "devops": ["devops", "sre", "\uc778\ud504\ub77c", "\ud074\ub77c\uc6b0\ub4dc", "kubernetes", "docker"],
    "mobile": ["\ubaa8\ubc14\uc77c", "android", "ios", "kotlin", "swift", "flutter"],
    "embedded": ["\uc784\ubca0\ub514\ub4dc", "firmware", "\ud38c\uc6e8\uc5b4", "c++"],
    "qa": ["qa", "\ud14c\uc2a4\ud2b8", "\ud488\uc9c8"],
    "security": ["\ubcf4\uc548", "security"],
}

DEVELOPER_ROLE_ALIASES = [
    "\uac1c\ubc1c",
    "developer",
    "engineer",
    "software",
    "s/w",
    "\uc18c\ud504\ud2b8\uc6e8\uc5b4",
    "\ubc31\uc5d4\ub4dc",
    "\ud504\ub860\ud2b8",
    "\ud480\uc2a4\ud0dd",
    "\uc11c\ubc84",
    "api",
    "python",
    "java",
    "react",
    "node",
    "spring",
    "devops",
    "sre",
    "\uc778\ud504\ub77c",
    "\ubaa8\ubc14\uc77c",
    "\uc784\ubca0\ub514\ub4dc",
]

NON_DEVELOPER_ROLE_ALIASES = [
    "pm",
    "po",
    "pl",
    "project manager",
    "product manager",
    "\ud504\ub85c\uc81d\ud2b8 \ub9e4\ub2c8\uc800",
    "\ud504\ub85c\ub355\ud2b8 \ub9e4\ub2c8\uc800",
    "\uc0ac\uc5c5\uac1c\ubc1c",
    "bd",
    "\uae30\uc220\uc601\uc5c5",
    "\uc601\uc5c5",
    "\uc601\uc5c5\uae30\ud68d",
    "\uc194\ub8e8\uc158\uae30\uc220\uc601\uc5c5",
    "cs",
    "\uace0\uac1d\uc9c0\uc6d0",
    "\ud5ec\ud504\ub370\uc2a4\ud06c",
    "\ud604\uc7a5\uc14b\uc5c5",
    "\ud604\uc7a5\uc9c0\uc6d0",
    "\uc720\uc9c0\ubcf4\uc218",
    "\ucee8\uc124\ud305",
]

NEGATION_MARKERS = [
    "\uac00 \uc544\ub2cc",
    "\uc774 \uc544\ub2cc",
    "\uc740 \uc544\ub2cc",
    "\ub294 \uc544\ub2cc",
    " \uc544\ub2cc",
    " \uc81c\uc678",
    " \ub9d0\uace0",
    " \ube7c\uace0",
    "\uc81c\uc678",
    "\ub9d0\uace0",
    "\ube7c\uace0",
]


@dataclass(frozen=True)
class QueryIntent:
    raw_query: str
    terms: list[str]
    regions: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    role_terms: list[str] = field(default_factory=list)
    excluded_roles: list[str] = field(default_factory=list)
    excluded_terms: list[str] = field(default_factory=list)
    deadline_types: list[str] = field(default_factory=list)
    experienced: bool = False
    require_analyzed: bool = False
    prefer_developer_roles: bool = True


def parse_query_intent(query: str) -> QueryIntent:
    normalized = _normalize(query)
    excluded_roles = _extract_excluded_roles(normalized)
    excluded_terms = _excluded_terms_for_roles(excluded_roles)
    terms = [term for term in _query_terms(normalized) if term not in set(excluded_terms)]
    regions = [region for region, aliases in REGION_ALIASES.items() if any(alias in normalized for alias in aliases)]
    skills = [skill for skill in TECH_KEYWORDS if skill in normalized and skill not in set(excluded_terms)]
    role_terms = [
        role
        for role, aliases in ROLE_KEYWORDS.items()
        if role not in excluded_roles and any(alias in normalized for alias in aliases)
    ]
    deadline_types = _extract_deadline_types(normalized)
    experienced = any(token in normalized for token in ["8\ub144", "9\ub144", "8-9", "8~9", "\uc2dc\ub2c8\uc5b4", "\uacbd\ub825"])
    require_analyzed = experienced or "\uc801\ud569" in normalized or "\ucd94\ucc9c" in normalized
    prefer_developer_roles = _should_prefer_developer_roles(normalized, role_terms)
    return QueryIntent(
        raw_query=query,
        terms=terms,
        regions=regions,
        skills=skills,
        role_terms=role_terms,
        excluded_roles=excluded_roles,
        excluded_terms=excluded_terms,
        deadline_types=deadline_types,
        experienced=experienced,
        require_analyzed=require_analyzed,
        prefer_developer_roles=prefer_developer_roles,
    )


def classify_deadline_text(deadline_text: str | None, deadline: str | None = None) -> str:
    combined = f"{deadline_text or ''} {deadline or ''}".replace(" ", "").lower()
    if not combined:
        return "unknown"
    if "\ucc44\uc6a9\uc2dc" in combined or "\ucc44\uc6a9\uc644\ub8cc\uc2dc" in combined:
        return "until_hired"
    if "\uc0c1\uc2dc" in combined:
        return "always_open"
    if combined.startswith("d-") or "d-" in combined or deadline:
        return "fixed_deadline"
    return "other"


def _extract_deadline_types(normalized: str) -> list[str]:
    deadline_types = []
    if "\ucc44\uc6a9\uc2dc" in normalized or "\ucc44\uc6a9 \uc2dc" in normalized:
        deadline_types.append("until_hired")
    if "\uc0c1\uc2dc" in normalized:
        deadline_types.append("always_open")
    if "d-" in normalized or "\ub9c8\uac10" in normalized or "\ub0a0\uc9dc" in normalized:
        deadline_types.append("fixed_deadline")
    return deadline_types


def _extract_excluded_roles(normalized: str) -> list[str]:
    excluded = []
    for role, aliases in ROLE_KEYWORDS.items():
        if any(_is_negated(alias, normalized) for alias in aliases):
            excluded.append(role)
    return sorted(set(excluded))


def _excluded_terms_for_roles(roles: list[str]) -> list[str]:
    terms: list[str] = []
    for role in roles:
        terms.extend(ROLE_KEYWORDS.get(role, []))
    return sorted(set(terms))


def _is_negated(alias: str, normalized: str) -> bool:
    compact = normalized.replace(" ", "")
    alias_compact = alias.replace(" ", "")
    if f"non{alias_compact}" in compact or f"not{alias_compact}" in compact:
        return True
    return any(f"{alias}{marker}" in normalized or f"{alias_compact}{marker.replace(' ', '')}" in compact for marker in NEGATION_MARKERS)


def _should_prefer_developer_roles(normalized: str, role_terms: list[str]) -> bool:
    if any(alias in normalized for alias in NON_DEVELOPER_ROLE_ALIASES):
        return False
    if role_terms:
        return True
    return any(token in normalized for token in ["\uacf5\uace0", "\ucc44\uc6a9", "\uc9c1\ubb34", "\uc77c\uc790\ub9ac", "\ucd94\ucc9c"])


def _query_terms(normalized: str) -> list[str]:
    raw_terms = [term.strip() for term in normalized.replace("/", " ").replace(",", " ").split()]
    return [term for term in raw_terms if len(term) >= 2]


def _normalize(query: str) -> str:
    return query.lower().replace("\u00b7", " ").replace("\u318d", " ")
