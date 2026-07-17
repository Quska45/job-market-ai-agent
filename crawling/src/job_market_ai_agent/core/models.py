from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class CompanyInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    url: HttpUrl | None = None
    size_type: str | None = None
    employee_count: str | None = None


class LocationInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str | None = None
    address: str | None = None
    region_level1: str | None = None
    region_level2: str | None = None


class JobInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str | None = None
    sub_categories: list[str] = Field(default_factory=list)
    position: str | None = None


class EmploymentInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str | None = None
    experience: str | None = None
    education: str | None = None


class PostingDates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    posted_at: str | None = None
    deadline: str | None = None
    deadline_text: str | None = None


class PostingContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str | None = None
    description: str | None = None
    raw_text: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    sections: dict[str, str] = Field(default_factory=dict)


class CrawlMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collected_at: datetime
    content_hash: str
    list_page: int | None = None


class JobPosting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    source_job_id: str
    url: HttpUrl
    title: str
    company: CompanyInfo
    location: LocationInfo = Field(default_factory=LocationInfo)
    job: JobInfo = Field(default_factory=JobInfo)
    skills: list[str] = Field(default_factory=list)
    employment: EmploymentInfo = Field(default_factory=EmploymentInfo)
    dates: PostingDates = Field(default_factory=PostingDates)
    content: PostingContent = Field(default_factory=PostingContent)
    crawl: CrawlMetadata





