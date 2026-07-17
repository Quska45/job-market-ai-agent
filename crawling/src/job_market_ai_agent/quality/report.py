from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any


REQUIRED_FIELD_PATHS = [
    "source",
    "source_job_id",
    "url",
    "title",
    "company.name",
    "location.summary",
    "job.sub_categories",
    "employment.experience",
    "dates.deadline_text",
    "content.description",
    "content.image_urls",
    "crawl.content_hash",
]


@dataclass(frozen=True)
class QualityReport:
    total_jobs: int
    field_fill_rates: dict[str, float]
    missing_counts: dict[str, int]
    description_min_length: int
    description_avg_length: float
    description_max_length: int
    jobs_with_images: int
    total_image_urls: int


def build_quality_report(rows: list[dict[str, Any]]) -> QualityReport:
    description_lengths = [
        len(_value_at_path(row, "content.description") or "")
        for row in rows
    ]
    image_counts = [
        len(_value_at_path(row, "content.image_urls") or [])
        for row in rows
    ]

    missing_counts = {
        path: sum(1 for row in rows if not _has_value(_value_at_path(row, path)))
        for path in REQUIRED_FIELD_PATHS
    }
    total = len(rows)
    field_fill_rates = {
        path: 0.0 if total == 0 else round((total - missing) / total, 4)
        for path, missing in missing_counts.items()
    }

    return QualityReport(
        total_jobs=total,
        field_fill_rates=field_fill_rates,
        missing_counts=missing_counts,
        description_min_length=min(description_lengths, default=0),
        description_avg_length=round(mean(description_lengths), 2) if description_lengths else 0.0,
        description_max_length=max(description_lengths, default=0),
        jobs_with_images=sum(1 for count in image_counts if count > 0),
        total_image_urls=sum(image_counts),
    )


def format_quality_report(report: QualityReport) -> str:
    lines = [
        "Job Data Quality Report",
        f"total_jobs: {report.total_jobs}",
        (
            "description_length: "
            f"min={report.description_min_length}, "
            f"avg={report.description_avg_length}, "
            f"max={report.description_max_length}"
        ),
        f"jobs_with_images: {report.jobs_with_images}",
        f"total_image_urls: {report.total_image_urls}",
        "",
        "field_fill_rates:",
    ]
    for path in REQUIRED_FIELD_PATHS:
        rate = report.field_fill_rates[path] * 100
        missing = report.missing_counts[path]
        lines.append(f"- {path}: {rate:.1f}% filled, missing={missing}")
    return "\n".join(lines)


def _value_at_path(row: dict[str, Any], path: str) -> Any:
    value: Any = row
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list | tuple | set | dict):
        return len(value) > 0
    return True

