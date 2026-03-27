from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.integrations import (
    IntegrationConnectRequest,
    IntegrationResponse,
    IntegrationSyncResult,
)
from backend.core.encryption import encrypt_payload
from backend.core.exceptions import NotFoundError, ServiceUnavailableError
from backend.db.models import Integration
from backend.db.models import utc_now
from backend.db.repositories.integration_repo import IntegrationRepository

from .base import BaseService


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
        item.last_synced_at = started_at
        try:
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return IntegrationSyncResult(
            provider=item.provider,
            status="success",
            synced_records=0,
            errors=0,
            started_at=started_at,
            finished_at=utc_now(),
        )
