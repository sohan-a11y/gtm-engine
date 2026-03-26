"""Hunter.io email enrichment and verification integration.

Docs: https://hunter.io/api-documentation/v2

Endpoints used:
  GET /v2/email-finder   — find a verified email for a person at a domain
  GET /v2/email-verifier — verify deliverability of a specific address
  GET /v2/domain-search  — list all emails found for a domain (used for enrichment)

Authentication: API key passed as the ``api_key`` query parameter.

Rate limits (free tier): 25 searches + 50 verifications / month.
On 429, raises RuntimeError so the enrichment_retry decorator in the
Celery task layer retries with a 60-second fixed delay (spec §7.3).
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from backend.integrations.data.base_enrichment import BaseEnrichmentClient

logger = logging.getLogger("gtm.integrations.hunter")

_BASE = "https://api.hunter.io"
_TIMEOUT = 20.0


class HunterClient(BaseEnrichmentClient):
    provider_name = "hunter"

    def __init__(self, *, api_key: str | None = None) -> None:
        self.api_key = api_key

    # ── enrich contact ────────────────────────────────────────────────────────

    async def enrich_contact(self, *, contact: dict[str, Any]) -> dict[str, Any]:
        """
        Attempt to find a verified work email for the contact.

        Strategy (in order of preference):
          1. If email already provided → verify it directly.
          2. If first_name + last_name + domain provided → use email-finder.
          3. If only domain provided → use domain-search to list known emails.
        """
        if not self.api_key:
            logger.warning("Hunter: no api_key configured — skipping enrichment")
            return {
                "provider": self.provider_name,
                "contact": contact,
                "data": {},
                "status": "skipped",
            }

        email = contact.get("email")
        first = contact.get("first_name")
        last = contact.get("last_name")
        domain = contact.get("domain") or _extract_domain(contact.get("company_email") or "")

        # ── path 1: verify existing email ──
        if email:
            result = await self.verify_email(email=email)
            return {
                "provider": self.provider_name,
                "contact": contact,
                "data": {"email_verification": result},
                "status": "enriched",
            }

        # ── path 2: find email by name + domain ──
        if first and last and domain:
            found = await self._find_email(first_name=first, last_name=last, domain=domain)
            return {
                "provider": self.provider_name,
                "contact": contact,
                "data": {"found_email": found},
                "status": "enriched" if found.get("email") else "not_found",
            }

        # ── path 3: domain search ──
        if domain:
            emails = await self._domain_search(domain=domain)
            return {
                "provider": self.provider_name,
                "contact": contact,
                "data": {"domain_emails": emails},
                "status": "enriched" if emails else "not_found",
            }

        return {
            "provider": self.provider_name,
            "contact": contact,
            "data": {},
            "status": "insufficient_data",
        }

    # ── verify email ──────────────────────────────────────────────────────────

    async def verify_email(self, *, email: str) -> dict[str, Any]:
        """
        Verify deliverability via Hunter's email-verifier endpoint.

        Hunter statuses:  valid | invalid | accept_all | webmail | disposable | unknown
        We map these to a [0.0, 1.0] score for the spec's email_risky flag.
        """
        if not self.api_key:
            return {"provider": self.provider_name, "email": email, "score": 0.5, "status": "unknown"}

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(
                    f"{_BASE}/v2/email-verifier",
                    params={"email": email, "api_key": self.api_key},
                )
                if resp.status_code == 429:
                    logger.warning("Hunter rate limited — will retry")
                    raise RuntimeError("Hunter rate limited (429)")
                resp.raise_for_status()
        except RuntimeError:
            raise
        except Exception as exc:
            logger.error("Hunter verify_email error: %s", exc)
            return {"provider": self.provider_name, "email": email, "score": 0.5, "status": "unknown"}

        data = resp.json().get("data", {})
        status = (data.get("status") or "unknown").lower()
        score_map = {
            "valid": 0.95,
            "accept_all": 0.70,
            "webmail": 0.65,
            "disposable": 0.10,
            "invalid": 0.0,
            "unknown": 0.50,
        }
        return {
            "provider": self.provider_name,
            "email": email,
            "score": score_map.get(status, 0.5),
            "status": status,
            "mx_records": data.get("mx_records"),
            "smtp_server": data.get("smtp_server"),
            "regexp": data.get("regexp"),
        }

    # ── private helpers ────────────────────────────────────────────────────────

    async def _find_email(
        self, *, first_name: str, last_name: str, domain: str
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(
                    f"{_BASE}/v2/email-finder",
                    params={
                        "domain": domain,
                        "first_name": first_name,
                        "last_name": last_name,
                        "api_key": self.api_key,
                    },
                )
                if resp.status_code == 429:
                    raise RuntimeError("Hunter rate limited (429)")
                resp.raise_for_status()
        except RuntimeError:
            raise
        except Exception as exc:
            logger.error("Hunter email-finder error: %s", exc)
            return {}

        data = resp.json().get("data", {})
        return {
            "email": data.get("email"),
            "score": data.get("score"),
            "sources": data.get("sources", []),
        }

    async def _domain_search(self, *, domain: str, limit: int = 10) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(
                    f"{_BASE}/v2/domain-search",
                    params={"domain": domain, "limit": limit, "api_key": self.api_key},
                )
                if resp.status_code == 429:
                    raise RuntimeError("Hunter rate limited (429)")
                resp.raise_for_status()
        except RuntimeError:
            raise
        except Exception as exc:
            logger.error("Hunter domain-search error: %s", exc)
            return []

        emails = resp.json().get("data", {}).get("emails", [])
        return [
            {
                "email": e.get("value"),
                "type": e.get("type"),
                "confidence": e.get("confidence"),
                "first_name": e.get("first_name"),
                "last_name": e.get("last_name"),
                "position": e.get("position"),
            }
            for e in emails
        ]


def _extract_domain(email: str) -> str:
    """Return the domain part of an email address, or empty string."""
    if "@" in email:
        return email.split("@", 1)[1].lower().strip()
    return ""
