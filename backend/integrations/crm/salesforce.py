"""Salesforce CRM integration — REST API v57.0.

Docs: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/

Authentication: OAuth2 Bearer access token. The caller must supply
``instance_url`` (e.g. https://yourorg.my.salesforce.com) and ``access_token``.
Token refresh is the caller's responsibility.

SOQL queries are used for reads (paginated via nextRecordsUrl).
PATCH /sobjects/ is used for updates.
POST /sobjects/Task/ is used for activity creation.
"""
from __future__ import annotations

import logging
from typing import Any
import httpx

from backend.integrations.crm.base_crm import BaseCRM

logger = logging.getLogger("gtm.integrations.salesforce")

_API_VERSION = "v57.0"
_TIMEOUT = 30.0

# Salesforce field → internal field (CRM-owned)
_CONTACT_MAP: dict[str, str] = {
    "FirstName": "first_name",
    "LastName": "last_name",
    "Email": "email",
    "Title": "title",
    "Account.Name": "company_name",
    "Phone": "phone",
    "MailingCity": "city",
    "MailingCountry": "country",
}

# Internal GTM field → Salesforce custom field (GTM-owned)
_SCORE_MAP: dict[str, str] = {
    "icp_score": "GTM_ICP_Score__c",
    "icp_score_reason": "GTM_ICP_Reason__c",
    "risk_score": "GTM_Deal_Risk__c",
    "health_score": "GTM_Health_Score__c",
}


class SalesforceCRM(BaseCRM):
    provider_name = "salesforce"

    def __init__(
        self,
        *,
        access_token: str | None = None,
        instance_url: str | None = None,
        field_mapping: dict[str, str] | None = None,
    ) -> None:
        self.access_token = access_token
        # Normalise: strip trailing slash
        self.instance_url = (instance_url or "").rstrip("/")
        self.field_mapping = {**_CONTACT_MAP, **(field_mapping or {})}

    # ── helpers ────────────────────────────────────────────────────────────────

    def _url(self, path: str) -> str:
        return f"{self.instance_url}/services/data/{_API_VERSION}/{path.lstrip('/')}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _map_contact(self, rec: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {"external_crm_id": rec.get("Id")}
        for sf_key, internal_key in self.field_mapping.items():
            # Support nested Account.Name via dot notation
            if "." in sf_key:
                parts = sf_key.split(".", 1)
                val = (rec.get(parts[0]) or {}).get(parts[1]) if rec.get(parts[0]) else None
            else:
                val = rec.get(sf_key)
            if val is not None:
                result[internal_key] = val
        return result

    def _map_account(self, rec: dict[str, Any]) -> dict[str, Any]:
        count = rec.get("NumberOfEmployees")
        return {
            "external_crm_id": rec.get("Id"),
            "name": rec.get("Name") or "",
            "domain": rec.get("Website"),
            "industry": rec.get("Industry"),
            "employee_count": int(count) if count else None,
        }

    def _map_opportunity(self, rec: dict[str, Any]) -> dict[str, Any]:
        amount = rec.get("Amount")
        return {
            "external_crm_id": rec.get("Id"),
            "name": rec.get("Name") or "",
            "stage": rec.get("StageName") or "prospecting",
            "amount_cents": int(float(amount) * 100) if amount else 0,
            "close_date": rec.get("CloseDate"),
        }

    # ── read operations ────────────────────────────────────────────────────────

    async def get_contacts(
        self, *, cursor: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        if not self.access_token or not self.instance_url:
            logger.warning("Salesforce: access_token or instance_url not configured")
            return []

        fields = "Id,FirstName,LastName,Email,Title,Phone,MailingCity,MailingCountry,Account.Name"
        soql = f"SELECT {fields} FROM Contact LIMIT {min(limit, 200)}"
        if cursor:
            # cursor is the nextRecordsUrl path returned by a previous call
            url = f"{self.instance_url}{cursor}" if cursor.startswith("/") else self._url(f"query?q={soql}")
        else:
            url = self._url(f"query?q={soql}")

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(url, headers=self._headers())
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Salesforce get_contacts HTTP %s: %s", exc.response.status_code, exc.response.text[:200])
            return []
        except Exception as exc:
            logger.error("Salesforce get_contacts error: %s", exc)
            return []

        return [self._map_contact(r) for r in resp.json().get("records", [])]

    async def get_companies(
        self, *, cursor: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        if not self.access_token or not self.instance_url:
            return []

        soql = f"SELECT Id,Name,Website,Industry,NumberOfEmployees FROM Account LIMIT {min(limit, 200)}"
        url = (
            f"{self.instance_url}{cursor}"
            if cursor and cursor.startswith("/")
            else self._url(f"query?q={soql}")
        )

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(url, headers=self._headers())
                resp.raise_for_status()
        except Exception as exc:
            logger.error("Salesforce get_companies error: %s", exc)
            return []

        return [self._map_account(r) for r in resp.json().get("records", [])]

    async def get_deals(
        self, *, cursor: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        if not self.access_token or not self.instance_url:
            return []

        soql = f"SELECT Id,Name,StageName,Amount,CloseDate FROM Opportunity LIMIT {min(limit, 200)}"
        url = (
            f"{self.instance_url}{cursor}"
            if cursor and cursor.startswith("/")
            else self._url(f"query?q={soql}")
        )

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(url, headers=self._headers())
                resp.raise_for_status()
        except Exception as exc:
            logger.error("Salesforce get_deals error: %s", exc)
            return []

        return [self._map_opportunity(r) for r in resp.json().get("records", [])]

    # ── write operations ───────────────────────────────────────────────────────

    async def update_contact(
        self, *, external_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        if not self.access_token or not self.instance_url:
            return {"provider": self.provider_name, "external_id": external_id, "status": "skipped"}

        sf_data: dict[str, Any] = {}
        for gtm_field, sf_field in _SCORE_MAP.items():
            if gtm_field in data and data[gtm_field] is not None:
                val = data[gtm_field]
                sf_data[sf_field] = str(val)[:255] if isinstance(val, str) else val

        # Pass through explicitly provided Salesforce-native fields
        for k, v in data.items():
            if k not in _SCORE_MAP and k != "external_crm_id":
                sf_data[k] = v

        if not sf_data:
            return {"provider": self.provider_name, "external_id": external_id, "status": "no_changes"}

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.patch(
                    self._url(f"sobjects/Contact/{external_id}"),
                    headers=self._headers(),
                    json=sf_data,
                )
                resp.raise_for_status()
                return {"provider": self.provider_name, "external_id": external_id, "status": "updated"}
        except httpx.HTTPStatusError as exc:
            logger.error("Salesforce update_contact %s HTTP %s: %s", external_id, exc.response.status_code, exc.response.text[:200])
            return {"provider": self.provider_name, "external_id": external_id, "status": "error", "detail": str(exc)}
        except Exception as exc:
            logger.error("Salesforce update_contact error: %s", exc)
            return {"provider": self.provider_name, "external_id": external_id, "status": "error", "detail": str(exc)}

    async def create_activity(
        self, *, external_contact_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a Salesforce Task linked to the Contact."""
        if not self.access_token or not self.instance_url:
            return {"provider": self.provider_name, "status": "skipped"}

        task: dict[str, Any] = {
            "WhoId": external_contact_id,
            "Subject": data.get("subject") or "GTM Engine Activity",
            "Description": data.get("body") or data.get("note") or str(data),
            "Status": "Completed",
            "ActivityDate": data.get("date") or "",
        }

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    self._url("sobjects/Task"),
                    headers=self._headers(),
                    json=task,
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
            logger.error("Salesforce create_activity error: %s", exc)
            return {"provider": self.provider_name, "status": "error", "detail": str(exc)}
