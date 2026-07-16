from __future__ import annotations

from abc import ABC, abstractmethod

from job_market_ai_agent.core.models import JobPosting


class JobCollector(ABC):
    @abstractmethod
    def collect(self) -> list[JobPosting]:
        """Collect job postings from a source."""

