from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EnrichmentResult:
    contact_id: str
    provider_results: dict[str, Any] = field(default_factory=dict)
    merged_data: dict[str, Any] = field(default_factory=dict)
    enrichment_status: str = "pending"


class ProfileEnricher:
    def __init__(self, *, apollo_client: Any | None = None, hunter_client: Any | None = None) -> None:
        self.apollo_client = apollo_client
        self.hunter_client = hunter_client

    async def enrich_contact(self, *, contact: dict[str, Any]) -> EnrichmentResult:
        provider_results: dict[str, Any] = {}
        merged_data: dict[str, Any] = {}

        if self.apollo_client is not None:
            provider_results["apollo"] = await self.apollo_client.enrich_contact(contact=contact)
            merged_data.update(provider_results["apollo"].get("data", {}))

        if self.hunter_client is not None and contact.get("email"):
            provider_results["hunter"] = await self.hunter_client.verify_email(email=str(contact["email"]))
            merged_data.setdefault("email_verification", {}).update(provider_results["hunter"])

        status = "enriched" if provider_results else "skipped"
        return EnrichmentResult(
            contact_id=str(contact.get("id", "")),
            provider_results=provider_results,
            merged_data=merged_data,
            enrichment_status=status,
        )
