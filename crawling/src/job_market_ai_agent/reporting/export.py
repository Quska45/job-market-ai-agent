from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any, Iterable


REPORT_COLUMNS = [
    "company",
    "title",
    "location",
    "address",
    "role_category",
    "seniority",
    "experience",
    "fit_for_8_9_year_developer",
    "career_fit_reason",
    "required_skills",
    "preferred_skills",
    "posted_at",
    "deadline",
    "deadline_text",
    "deadline_type",
    "url",
]


def load_jobs(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
        return payload["jobs"]
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Expected a JSON array or object with jobs: {path}")


def build_report_rows(jobs: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    return [_build_report_row(job) for job in jobs]


def export_csv(rows: list[dict[str, str]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=REPORT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def export_markdown(rows: list[dict[str, str]]) -> str:
    header = "| " + " | ".join(REPORT_COLUMNS) + " |"
    separator = "| " + " | ".join(["---"] * len(REPORT_COLUMNS)) + " |"
    lines = [header, separator]
    for row in rows:
        values = [_escape_markdown(row.get(column, "")) for column in REPORT_COLUMNS]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def write_report(input_path: Path, output_path: Path, output_format: str) -> Path:
    rows = build_report_rows(load_jobs(input_path))
    if output_format == "csv":
        content = export_csv(rows)
    elif output_format == "markdown":
        content = export_markdown(rows)
    else:
        raise ValueError(f"Unsupported report format: {output_format}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    encoding = "utf-8-sig" if output_format == "csv" else "utf-8"
    output_path.write_text(content, encoding=encoding)
    return output_path


def default_output_path(input_path: Path, output_format: str) -> Path:
    extension = "csv" if output_format == "csv" else "md"
    return Path("data") / "reports" / f"{input_path.stem}_analysis_report.{extension}"


def _build_report_row(job: dict[str, Any]) -> dict[str, str]:
    company = job.get("company") or {}
    location = job.get("location") or {}
    employment = job.get("employment") or {}
    dates = job.get("dates") or {}
    analysis = job.get("analysis") or {}

    required_skills = _join_values(analysis.get("required_skills") or job.get("skills") or [])
    preferred_skills = _join_values(analysis.get("preferred_skills") or [])

    return {
        "company": _string(company.get("name")),
        "title": _string(job.get("title")),
        "location": _string(location.get("summary")),
        "address": _string(location.get("address")),
        "role_category": _string(analysis.get("role_category")),
        "seniority": _string(analysis.get("seniority")),
        "experience": _string(employment.get("experience")),
        "fit_for_8_9_year_developer": _format_score(analysis.get("fit_for_8_9_year_developer")),
        "career_fit_reason": _string(analysis.get("career_fit_reason")),
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "posted_at": _string(dates.get("posted_at")),
        "deadline": _string(dates.get("deadline")),
        "deadline_text": _string(dates.get("deadline_text")),
        "deadline_type": classify_deadline(dates),
        "url": _string(job.get("url")),
    }


def classify_deadline(dates: dict[str, Any]) -> str:
    deadline_text = _string(dates.get("deadline_text"))
    deadline = _string(dates.get("deadline"))
    combined = f"{deadline_text} {deadline}".replace(" ", "")
    if not combined:
        return "unknown"
    if "채용시" in combined or "채용완료시" in combined:
        return "until_hired"
    if "상시" in combined:
        return "always_open"
    if deadline_text.startswith("D-") or deadline:
        return "fixed_deadline"
    return "other"


def _join_values(values: Iterable[Any]) -> str:
    return ", ".join(_string(value) for value in values if _string(value))


def _format_score(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{value:.2f}"
    return ""


def _string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _escape_markdown(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")

