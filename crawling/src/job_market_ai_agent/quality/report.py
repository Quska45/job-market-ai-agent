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
    overall_fill_rate: float
    overall_score: float
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
    filled_values = sum(total - missing for missing in missing_counts.values())
    total_values = total * len(REQUIRED_FIELD_PATHS)
    overall_fill_rate = 0.0 if total_values == 0 else round(filled_values / total_values, 4)

    return QualityReport(
        total_jobs=total,
        overall_fill_rate=overall_fill_rate,
        overall_score=round(overall_fill_rate * 100, 2),
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
        f"overall_score: {report.overall_score:.2f}%",
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




def build_job_quality(row: dict[str, Any]) -> dict[str, object]:
    missing_fields = [
        path for path in REQUIRED_FIELD_PATHS
        if not _has_value(_value_at_path(row, path))
    ]
    total_fields = len(REQUIRED_FIELD_PATHS)
    filled_fields = total_fields - len(missing_fields)
    fill_rate = 0.0 if total_fields == 0 else round(filled_fields / total_fields, 4)
    description = _value_at_path(row, "content.description") or ""
    image_urls = _value_at_path(row, "content.image_urls") or []
    return {
        "score": round(fill_rate * 100, 2),
        "fill_rate": fill_rate,
        "filled_fields": filled_fields,
        "total_fields": total_fields,
        "missing_fields": missing_fields,
        "description_length": len(description),
        "image_count": len(image_urls),
        "has_required_content": bool(description.strip()),
    }


def attach_job_quality(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"quality": build_job_quality(row), **row}
        for row in rows
    ]
def quality_report_to_dict(report: QualityReport) -> dict[str, object]:
    return {
        "total_jobs": report.total_jobs,
        "overall_score": report.overall_score,
        "overall_fill_rate": report.overall_fill_rate,
        "description_length": {
            "min": report.description_min_length,
            "avg": report.description_avg_length,
            "max": report.description_max_length,
        },
        "jobs_with_images": report.jobs_with_images,
        "total_image_urls": report.total_image_urls,
        "field_fill_rates": report.field_fill_rates,
        "missing_counts": report.missing_counts,
    }


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

