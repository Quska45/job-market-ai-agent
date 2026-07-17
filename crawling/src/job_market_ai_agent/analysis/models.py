from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class JobAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_category: str
    seniority: str
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    main_tasks: list[str] = Field(default_factory=list)
    domain: str | None = None
    fit_for_beginner: float = Field(default=0.0, ge=0.0, le=1.0)
    fit_for_8_9_year_developer: float = Field(default=0.0, ge=0.0, le=1.0)
    career_fit_reason: str = ""
    senior_keywords: list[str] = Field(default_factory=list)
    summary: str
    evidence: list[str] = Field(default_factory=list)


class AnalyzedJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_job_id: str
    title: str
    company_name: str
    analysis: JobAnalysis
