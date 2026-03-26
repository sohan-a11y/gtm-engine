"""Apollo.io enrichment integration.

Docs: https://apolloio.github.io/apollo-api-docs/

Endpoints used:
  POST /v1/people/match   — enrich a contact by email or name + domain
  POST /v1/email_accounts/email_account_information — verify email deliverability

Authentication: API key passed as ``api_key`` query parameter or in the
request body (Apollo accepts both).

Rate limits (free tier): 50 requests / hour. The spec mandates a fixed 60-second
retry on 429 responses (handled by the Celery task layer via enrichment_retry).
This client raises a plain exception on 429 so the retry decorator triggers.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from backend.integrations.data.base_enrichment import BaseEnrichmentClient

logger = logging.getLogger("gtm.integrations.apollo")

_BASE = "https://api.apollo.io"
_TIMEOUT = 20.0


class ApolloClient(BaseEnrichmentClient):
    provider_name = "apollo"

    def __init__(self, *, api_key: str | None = None) -> None:
        self.api_key = api_key

    # ── helpers ────────────────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

    # ── enrich contact ────────────────────────────────────────────────────────

    async def enrich_contact(self, *, contact: dict[str, Any]) -> dict[str, Any]:
        """
        Match a person record using Apollo's /people/match endpoint.

        Accepts any combination of: email, first_name + last_name + domain,
        linkedin_url. The more fields provided the higher the match confidence.
        """
        if not self.api_key:
            logger.warning("Apollo: no api_key configured — skipping enrichment")
            return {
                "provider": self.provider_name,
                "contact": contact,
                "data": {},
                "status": "skipped",
            }

        payload: dict[str, Any] = {"api_key": self.api_key}
        if contact.get("email"):
            payload["email"] = contact["email"]
        if contact.get("first_name"):
            payload["first_name"] = contact["first_name"]
        if contact.get("last_name"):
            payload["last_name"] = contact["last_name"]
        # Apollo accepts domain or company name for matching
        if contact.get("domain"):
            payload["domain"] = contact["domain"]
        elif contact.get("company_name") or contact.get("company"):
            payload["organization_name"] = contact.get("company_name") or contact.get("company")
        if contact.get("linkedin_url"):
            payload["linkedin_url"] = contact["linkedin_url"]

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    f"{_BASE}/v1/people/match",
                    headers=self._headers(),
                    json=payload,
                )
                if resp.status_code == 429:
                    logger.warning("Apollo rate limited — will retry")
                    raise RuntimeError("Apollo rate limited (429)")
                resp.raise_for_status()
        except RuntimeError:
            raise
        except httpx.HTTPStatusError as exc:
            logger.error("Apollo enrich HTTP %s: %s", exc.response.status_code, exc.response.text[:200])
            return {"provider": self.provider_name, "contact": contact, "data": {}, "status": "error"}
        except Exception as exc:
            logger.error("Apollo enrich error: %s", exc)
            return {"provider": self.provider_name, "contact": contact, "data": {}, "status": "error"}

        person = resp.json().get("person") or {}
        org = person.get("organization") or {}

        enriched: dict[str, Any] = {
            "title": person.get("title"),
            "seniority": person.get("seniority"),
            "department": person.get("departments", [None])[0] if person.get("departments") else None,
            "linkedin_url": person.get("linkedin_url"),
            "city": person.get("city"),
            "country": person.get("country"),
            "company_name": org.get("name"),
            "company_size": org.get("estimated_num_employees"),
            "company_industry": org.get("industry"),
            "company_domain": org.get("primary_domain"),
            "company_linkedin_url": org.get("linkedin_url"),
            "tech_stack": org.get("technology_names") or [],
            "funding_stage": org.get("latest_funding_stage"),
            "total_funding_usd": org.get("total_funding"),
        }
        # Strip None values to keep the enrichment_data JSONB clean
        enriched = {k: v for k, v in enriched.items() if v is not None}

        return {
            "provider": self.provider_name,
            "contact": contact,
            "data": enriched,
            "status": "enriched",
        }

    # ── verify email ──────────────────────────────────────────────────────────

    async def verify_email(self, *, email: str) -> dict[str, Any]:
        """
        Verify an email address using Apollo's email verification endpoint.

        Returns a score in [0.0, 1.0] and a status string:
          valid / risky / invalid / unknown
        """
        if not self.api_key:
            return {"provider": self.provider_name, "email": email, "score": 0.5, "status": "unknown"}

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    f"{_BASE}/v1/email_accounts/email_account_information",
                    headers=self._headers(),
                    json={"api_key": self.api_key, "email": email},
                )
                if resp.status_code == 429:
                    raise RuntimeError("Apollo rate limited (429)")
                resp.raise_for_status()
        except RuntimeError:
            raise
        except Exception as exc:
            logger.error("Apollo verify_email error: %s", exc)
            return {"provider": self.provider_name, "email": email, "score": 0.5, "status": "unknown"}

        data = resp.json()
        # Apollo returns deliverability: "deliverable" | "undeliverable" | "risky" | "unknown"
        deliverability = (data.get("deliverability") or "unknown").lower()
        score_map = {"deliverable": 0.95, "risky": 0.45, "undeliverable": 0.0, "unknown": 0.5}
        status_map = {"deliverable": "valid", "risky": "risky", "undeliverable": "invalid", "unknown": "unknown"}

        return {
            "provider": self.provider_name,
            "email": email,
            "score": score_map.get(deliverability, 0.5),
            "status": status_map.get(deliverability, "unknown"),
            "deliverability": deliverability,
        }
