from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SocialSignal:
    company: str
    source: str = "linkedin"
    details: dict[str, Any] = field(default_factory=dict)


class SocialScraper:
    async def scrape_company_signals(self, *, company_name: str, company_url: str | None = None) -> SocialSignal:
        details = {
            "company_url": company_url,
            "recent_activity": [],
            "hiring_signals": [],
            "tech_stack": [],
        }
        return SocialSignal(company=company_name, details=details)
