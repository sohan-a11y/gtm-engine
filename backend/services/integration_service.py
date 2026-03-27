from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.integrations import (
    IntegrationConnectRequest,
    IntegrationResponse,
    IntegrationSyncResult,
)
from backend.core.encryption import decrypt_payload, encrypt_payload
from backend.core.exceptions import NotFoundError, ServiceUnavailableError
from backend.db.models import Integration
from backend.db.models import utc_now
from backend.db.repositories.company_repo import CompanyRepository
from backend.db.repositories.contact_repo import ContactRepository
from backend.db.repositories.deal_repo import DealRepository
from backend.db.repositories.integration_repo import IntegrationRepository

from .base import BaseService

logger = logging.getLogger("gtm.integrations")


def _integration_to_response(item: Integration) -> IntegrationResponse:
    return IntegrationResponse(
        id=str(item.id),
        org_id=str(item.org_id),
        provider=item.provider,
        status=item.status,
        credentials={},
        metadata=item.metadata_json or {},
        last_synced_at=item.last_synced_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@dataclass(slots=True)
class IntegrationService(BaseService):
    async def connect(self, org_id: str, request: IntegrationConnectRequest, *, session: AsyncSession) -> IntegrationResponse:
        repo = IntegrationRepository(session)
        payload = {
            "provider": request.provider,
            "integration_type": "generic",
            "status": "connected",
            "credentials_encrypted": encrypt_payload(request.credentials),
            "metadata_json": request.metadata,
        }
        try:
            # Upsert: if provider already exists for org, update it
            existing = await repo.get_by_provider(org_id=UUID(org_id), provider=request.provider)
            if existing is not None:
                existing.credentials_encrypted = payload["credentials_encrypted"]
                existing.metadata_json = payload["metadata_json"]
                existing.status = "connected"
                await session.commit()
                return _integration_to_response(existing)
            item = await repo.create(org_id=UUID(org_id), data=payload)
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return _integration_to_response(item)

    async def list_integrations(self, org_id: str, *, session: AsyncSession) -> list[IntegrationResponse]:
        repo = IntegrationRepository(session)
        try:
            items = await repo.list(org_id=UUID(org_id))
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return [_integration_to_response(i) for i in items]

    async def disconnect(self, org_id: str, integration_id: str, *, session: AsyncSession) -> IntegrationResponse:
        repo = IntegrationRepository(session)
        try:
            item = await repo.get(org_id=UUID(org_id), object_id=UUID(integration_id))
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if item is None:
            raise NotFoundError("Integration not found")
        item.status = "disconnected"
        try:
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return _integration_to_response(item)

    async def sync(self, org_id: str, integration_id: str, *, session: AsyncSession) -> IntegrationSyncResult:
        repo = IntegrationRepository(session)
        try:
            item = await repo.get(org_id=UUID(org_id), object_id=UUID(integration_id))
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if item is None:
            raise NotFoundError("Integration not found")

        started_at = utc_now()
        synced = 0
        errors = 0

        # Dispatch to the provider-specific sync handler
        try:
            if item.provider == "hubspot":
                synced, errors = await self._sync_hubspot(org_id=UUID(org_id), item=item, session=session)
            elif item.provider == "salesforce":
                synced, errors = await self._sync_salesforce(org_id=UUID(org_id), item=item, session=session)
        except Exception as exc:
            logger.error("Sync error for %s/%s: %s", item.provider, integration_id, exc)
            errors += 1

        item.last_synced_at = started_at
        try:
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc

        return IntegrationSyncResult(
            provider=item.provider,
            status="success" if errors == 0 else "partial",
            synced_records=synced,
            errors=errors,
            started_at=started_at,
            finished_at=utc_now(),
        )

    async def _sync_hubspot(self, *, org_id: UUID, item: Integration, session: AsyncSession) -> tuple[int, int]:
        """Pull contacts, companies, and deals from HubSpot and upsert into DB."""
        from backend.integrations.crm.hubspot import HubSpotCRM

        if not item.credentials_encrypted:
            logger.warning("HubSpot sync: no credentials stored for org %s", org_id)
            return 0, 0

        try:
            creds: dict = decrypt_payload(item.credentials_encrypted)
        except Exception as exc:
            logger.error("HubSpot sync: failed to decrypt credentials: %s", exc)
            return 0, 1

        access_token = creds.get("access_token", "")
        if not access_token:
            return 0, 0

        crm = HubSpotCRM(access_token=access_token)
        contact_repo = ContactRepository(session)
        company_repo = CompanyRepository(session)
        deal_repo = DealRepository(session)
        synced = 0
        errors = 0

        # ── contacts ──────────────────────────────────────────────────────────
        try:
            contacts = await crm.get_contacts(limit=100)
            for c in contacts:
                try:
                    email = c.get("email")
                    if not email:
                        continue
                    existing = await contact_repo.get_by_email(org_id=org_id, email=email)
                    if existing is None:
                        await contact_repo.create(org_id=org_id, data={
                            "email": email,
                            "first_name": c.get("first_name", ""),
                            "last_name": c.get("last_name", ""),
                            "title": c.get("title"),
                            "external_crm_id": c.get("external_crm_id"),
                            "enrichment_data": {k: v for k, v in c.items() if k not in ("email", "first_name", "last_name", "title", "external_crm_id")},
                        })
                    else:
                        existing.first_name = c.get("first_name", existing.first_name)
                        existing.last_name = c.get("last_name", existing.last_name)
                        existing.title = c.get("title") or existing.title
                        existing.external_crm_id = c.get("external_crm_id") or existing.external_crm_id
                    synced += 1
                except Exception as exc:
                    logger.debug("HubSpot contact upsert error: %s", exc)
                    errors += 1
        except Exception as exc:
            logger.error("HubSpot get_contacts error: %s", exc)
            errors += 1

        # ── companies ─────────────────────────────────────────────────────────
        try:
            companies = await crm.get_companies(limit=100)
            for co in companies:
                try:
                    name = co.get("name", "")
                    domain = co.get("domain")
                    if not name:
                        continue
                    existing = await company_repo.get_by_domain(org_id=org_id, domain=domain) if domain else None
                    if existing is None:
                        await company_repo.create(org_id=org_id, data={
                            "name": name,
                            "domain": domain,
                            "industry": co.get("industry"),
                            "employee_count": co.get("employee_count"),
                            "external_crm_id": co.get("external_crm_id"),
                        })
                    else:
                        existing.name = name
                        existing.industry = co.get("industry") or existing.industry
                        existing.employee_count = co.get("employee_count") or existing.employee_count
                    synced += 1
                except Exception as exc:
                    logger.debug("HubSpot company upsert error: %s", exc)
                    errors += 1
        except Exception as exc:
            logger.error("HubSpot get_companies error: %s", exc)
            errors += 1

        # ── deals ─────────────────────────────────────────────────────────────
        try:
            deals = await crm.get_deals(limit=100)
            for d in deals:
                try:
                    name = d.get("name", "")
                    if not name:
                        continue
                    await deal_repo.create(org_id=org_id, data={
                        "name": name,
                        "stage": d.get("stage", "prospecting"),
                        "amount_cents": d.get("amount_cents", 0),
                        "external_crm_id": d.get("external_crm_id"),
                    })
                    synced += 1
                except Exception as exc:
                    logger.debug("HubSpot deal upsert error: %s", exc)
                    errors += 1
        except Exception as exc:
            logger.error("HubSpot get_deals error: %s", exc)
            errors += 1

        return synced, errors

    async def _sync_salesforce(self, *, org_id: UUID, item: Integration, session: AsyncSession) -> tuple[int, int]:
        """Pull contacts, companies, and deals from Salesforce and upsert into DB."""
        from backend.integrations.crm.salesforce import SalesforceCRM

        if not item.credentials_encrypted:
            logger.warning("Salesforce sync: no credentials for org %s", org_id)
            return 0, 0

        try:
            creds: dict = decrypt_payload(item.credentials_encrypted)
        except Exception as exc:
            logger.error("Salesforce sync: failed to decrypt credentials: %s", exc)
            return 0, 1

        access_token = creds.get("access_token", "")
        instance_url = creds.get("instance_url", "")
        if not access_token or not instance_url:
            return 0, 0

        crm = SalesforceCRM(access_token=access_token, instance_url=instance_url)
        contact_repo = ContactRepository(session)
        company_repo = CompanyRepository(session)
        deal_repo = DealRepository(session)
        synced: int = 0
        errors: int = 0

        # ── contacts ──────────────────────────────────────────────────────────
        try:
            contacts = await crm.get_contacts(limit=100)
            for c in contacts:
                try:
                    email = c.get("email")
                    if not email:
                        continue
                    sf_existing = await contact_repo.get_by_email(org_id=org_id, email=email)
                    if sf_existing is None:
                        await contact_repo.create(org_id=org_id, data={
                            "email": email,
                            "first_name": c.get("first_name", ""),
                            "last_name": c.get("last_name", ""),
                            "title": c.get("title"),
                            "external_crm_id": c.get("external_crm_id"),
                        })
                    else:
                        sf_existing.first_name = c.get("first_name", sf_existing.first_name)
                        sf_existing.last_name = c.get("last_name", sf_existing.last_name)
                        sf_existing.external_crm_id = c.get("external_crm_id") or sf_existing.external_crm_id
                    synced += 1
                except Exception as exc:
                    logger.debug("Salesforce contact upsert error: %s", exc)
                    errors += 1
        except Exception as exc:
            logger.error("Salesforce get_contacts error: %s", exc)
            errors += 1

        # ── companies ─────────────────────────────────────────────────────────
        try:
            companies = await crm.get_companies(limit=100)
            for co in companies:
                try:
                    name = co.get("name", "")
                    if not name:
                        continue
                    domain = co.get("domain")
                    sf_co_existing = await company_repo.get_by_domain(org_id=org_id, domain=domain) if domain else None
                    if sf_co_existing is None:
                        await company_repo.create(org_id=org_id, data={
                            "name": name,
                            "domain": domain,
                            "industry": co.get("industry"),
                            "employee_count": co.get("employee_count"),
                            "external_crm_id": co.get("external_crm_id"),
                        })
                    else:
                        sf_co_existing.name = name
                    synced += 1
                except Exception as exc:
                    logger.debug("Salesforce company upsert error: %s", exc)
                    errors += 1
        except Exception as exc:
            logger.error("Salesforce get_companies error: %s", exc)
            errors += 1

        # ── deals ─────────────────────────────────────────────────────────────
        try:
            deals = await crm.get_deals(limit=100)
            for d in deals:
                try:
                    name = d.get("name", "")
                    if not name:
                        continue
                    await deal_repo.create(org_id=org_id, data={
                        "name": name,
                        "stage": d.get("stage", "prospecting"),
                        "amount_cents": d.get("amount_cents", 0),
                        "external_crm_id": d.get("external_crm_id"),
                    })
                    synced += 1
                except Exception as exc:
                    logger.debug("Salesforce deal upsert error: %s", exc)
                    errors += 1
        except Exception as exc:
            logger.error("Salesforce get_deals error: %s", exc)
            errors += 1

        return synced, errors
