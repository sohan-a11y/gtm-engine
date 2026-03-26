from __future__ import annotations

from typing import Any

from backend.integrations.data.base_enrichment import BaseEnrichmentClient


class LinkedInClient(BaseEnrichmentClient):
    provider_name = "linkedin"

    def __init__(self, *, api_key: str | None = None) -> None:
        self.api_key = api_key

    async def enrich_contact(self, *, contact: dict[str, Any]) -> dict[str, Any]:
        return {"provider": self.provider_name, "contact": contact, "data": {"social_profile": contact.get("linkedin_url")}}

    async def verify_email(self, *, email: str) -> dict[str, Any]:
        return {"provider": self.provider_name, "email": email, "status": "unsupported"}
