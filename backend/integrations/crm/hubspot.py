"""HubSpot CRM integration — REST API v3.

Docs: https://developers.hubspot.com/docs/api/crm/contacts

Authentication: Private App access token (Bearer) or OAuth2 access token.
The caller is responsible for token refresh; this client uses whatever token
it is initialised with.

Conflict-resolution rules (spec section 2.4):
- CRM-owned fields (firstname, lastname, email, jobtitle, company): CRM wins.
- GTM-owned fields (gtm_engine_icp_score, etc.): GTM wins on outbound sync.
- enrichment_data is never pushed to HubSpot.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from backend.integrations.crm.base_crm import BaseCRM

logger = logging.getLogger("gtm.integrations.hubspot")

_BASE = "https://api.hubapi.com"
_TIMEOUT = 30.0

# HubSpot property → internal field (CRM-owned; CRM wins on inbound sync)
_CONTACT_PROPS = [
    "firstname", "lastname", "email", "jobtitle", "company",
    "phone", "city", "country", "website", "hs_object_id",
]
_CONTACT_MAP: dict[str, str] = {
    "firstname": "first_name",
    "lastname": "last_name",
    "email": "email",
    "jobtitle": "title",
    "company": "company_name",
    "phone": "phone",
    "city": "city",
    "country": "country",
    "website": "website",
}

# Internal GTM field → HubSpot custom property (GTM-owned; pushed back to CRM)
_SCORE_MAP: dict[str, str] = {
    "icp_score": "gtm_engine_icp_score",
    "icp_score_reason": "gtm_engine_icp_reason",
    "risk_score": "gtm_engine_deal_risk",
    "health_score": "gtm_engine_health_score",
}


class HubSpotCRM(BaseCRM):
    provider_name = "hubspot"

    def __init__(
        self,
        *,
        access_token: str | None = None,
        field_mapping: dict[str, str] | None = None,
    ) -> None:
        self.access_token = access_token
        # Allow callers to override individual field mappings
        self.field_mapping = {**_CONTACT_MAP, **(field_mapping or {})}

    # ── private helpers ────────────────────────────────────────────────────────

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _map_contact(self, obj: dict[str, Any]) -> dict[str, Any]:
        props = obj.get("properties", obj)
        result: dict[str, Any] = {"external_crm_id": obj.get("id") or props.get("hs_object_id")}
        for hs_key, internal_key in self.field_mapping.items():
            val = props.get(hs_key)
            if val is not None:
                result[internal_key] = val
        return result

    def _map_company(self, obj: dict[str, Any]) -> dict[str, Any]:
        props = obj.get("properties", obj)
        count = props.get("numberofemployees")
        return {
            "external_crm_id": obj.get("id") or props.get("hs_object_id"),
            "name": props.get("name") or props.get("company") or "",
            "domain": props.get("domain"),
            "industry": props.get("industry"),
            "employee_count": int(count) if count else None,
        }

    def _map_deal(self, obj: dict[str, Any]) -> dict[str, Any]:
        props = obj.get("properties", obj)
        amount = props.get("amount")
        return {
            "external_crm_id": obj.get("id") or props.get("hs_object_id"),
            "name": props.get("dealname") or "",
            "stage": props.get("dealstage") or "prospecting",
            "amount_cents": int(float(amount) * 100) if amount else 0,
            "close_date": props.get("closedate"),
        }

    # ── read operations ────────────────────────────────────────────────────────

    async def get_contacts(
        self, *, cursor: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        if not self.access_token:
            logger.warning("HubSpot: no access_token configured — skipping contact fetch")
            return []

        params: dict[str, Any] = {
            "limit": min(limit, 100),
            "properties": ",".join(_CONTACT_PROPS),
        }
        if cursor:
            params["after"] = cursor

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(
                    f"{_BASE}/crm/v3/objects/contacts",
                    headers=self._auth_headers(),
                    params=params,
                )
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("HubSpot get_contacts HTTP %s: %s", exc.response.status_code, exc.response.text[:200])
            return []
        except Exception as exc:
            logger.error("HubSpot get_contacts error: %s", exc)
            return []

        return [
            self._map_contact({"id": r.get("id"), "properties": r.get("properties", {})})
            for r in resp.json().get("results", [])
        ]

    async def get_companies(
        self, *, cursor: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        if not self.access_token:
            return []

        params: dict[str, Any] = {
            "limit": min(limit, 100),
            "properties": "name,domain,industry,numberofemployees,hs_object_id",
        }
        if cursor:
            params["after"] = cursor

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(
                    f"{_BASE}/crm/v3/objects/companies",
                    headers=self._auth_headers(),
                    params=params,
                )
                resp.raise_for_status()
        except Exception as exc:
            logger.error("HubSpot get_companies error: %s", exc)
            return []

        return [
            self._map_company({"id": r.get("id"), "properties": r.get("properties", {})})
            for r in resp.json().get("results", [])
        ]

    async def get_deals(
        self, *, cursor: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        if not self.access_token:
            return []

        params: dict[str, Any] = {
            "limit": min(limit, 100),
            "properties": "dealname,dealstage,amount,closedate,hs_object_id",
        }
        if cursor:
            params["after"] = cursor

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(
                    f"{_BASE}/crm/v3/objects/deals",
                    headers=self._auth_headers(),
                    params=params,
                )
                resp.raise_for_status()
        except Exception as exc:
            logger.error("HubSpot get_deals error: %s", exc)
            return []

        return [
            self._map_deal({"id": r.get("id"), "properties": r.get("properties", {})})
            for r in resp.json().get("results", [])
        ]

    # ── write operations ───────────────────────────────────────────────────────

    async def update_contact(
        self, *, external_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        if not self.access_token:
            logger.warning("HubSpot: no access_token — skipping contact update for %s", external_id)
            return {"provider": self.provider_name, "external_id": external_id, "status": "skipped"}

        # Map GTM score fields → HubSpot custom properties
        hs_props: dict[str, Any] = {}
        for gtm_field, hs_field in _SCORE_MAP.items():
            if gtm_field in data and data[gtm_field] is not None:
                val = data[gtm_field]
                # Truncate string values to 500 chars (HubSpot single-line property limit)
                hs_props[hs_field] = val[:500] if isinstance(val, str) else val

        # Pass through any CRM-native properties that were explicitly provided
        for k, v in data.items():
            if k not in _SCORE_MAP and k not in ("external_crm_id",):
                hs_props[k] = v

        if not hs_props:
            return {"provider": self.provider_name, "external_id": external_id, "status": "no_changes"}

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.patch(
                    f"{_BASE}/crm/v3/objects/contacts/{external_id}",
                    headers=self._auth_headers(),
                    json={"properties": hs_props},
                )
                resp.raise_for_status()
                return {"provider": self.provider_name, "external_id": external_id, "status": "updated"}
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HubSpot update_contact %s HTTP %s: %s",
                external_id, exc.response.status_code, exc.response.text[:200],
            )
            return {"provider": self.provider_name, "external_id": external_id, "status": "error", "detail": str(exc)}
        except Exception as exc:
            logger.error("HubSpot update_contact error: %s", exc)
            return {"provider": self.provider_name, "external_id": external_id, "status": "error", "detail": str(exc)}

    async def create_activity(
        self, *, external_contact_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a NOTE engagement associated with the contact."""
        if not self.access_token:
            return {"provider": self.provider_name, "status": "skipped"}

        note_body = data.get("body") or data.get("note") or str(data)
        payload: dict[str, Any] = {
            "properties": {
                "hs_note_body": note_body[:10000],  # HubSpot note body limit
                "hs_timestamp": data.get("timestamp") or "",
            },
            "associations": [
                {
                    "to": {"id": external_contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 202,  # note → contact
                        }
                    ],
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    f"{_BASE}/crm/v3/objects/notes",
                    headers=self._auth_headers(),
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()
                return {
                    "provider": self.provider_name,
                    "external_contact_id": external_contact_id,
                    "activity_id": result.get("id"),
                    "status": "created",
                }
        except Exception as exc:
            logger.error("HubSpot create_activity error: %s", exc)
            return {"provider": self.provider_name, "status": "error", "detail": str(exc)}
