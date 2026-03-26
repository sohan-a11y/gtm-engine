from __future__ import annotations

from dataclasses import dataclass

from backend.api.schemas.integrations import (
    IntegrationConnectRequest,
    IntegrationResponse,
    IntegrationSyncResult,
)
from backend.core.encryption import encrypt_payload
from backend.core.exceptions import NotFoundError

from .base import BaseService
from .state import generate_id, utc_now


@dataclass(slots=True)
class IntegrationService(BaseService):
    async def connect(self, org_id: str, request: IntegrationConnectRequest) -> IntegrationResponse:
        integration_id = generate_id("integration")
        now = utc_now()
        record = {
            "id": integration_id,
            "org_id": org_id,
            "provider": request.provider,
            "status": "connected",
            "credentials": {"encrypted": encrypt_payload(request.credentials)},
            "metadata": request.metadata,
            "last_synced_at": None,
            "created_at": now,
            "updated_at": now,
        }
        self.state.integrations[integration_id] = record
        return IntegrationResponse.model_validate(record)

    async def list_integrations(self, org_id: str) -> list[IntegrationResponse]:
        return [
            IntegrationResponse.model_validate(item)
            for item in self.state.integrations.values()
            if item["org_id"] == org_id
        ]

    async def disconnect(self, org_id: str, integration_id: str) -> IntegrationResponse:
        item = self.state.integrations.get(integration_id)
        if not item or item["org_id"] != org_id:
            raise NotFoundError("Integration not found")
        item["status"] = "disconnected"
        item["updated_at"] = utc_now()
        return IntegrationResponse.model_validate(item)

    async def sync(self, org_id: str, integration_id: str) -> IntegrationSyncResult:
        item = self.state.integrations.get(integration_id)
        if not item or item["org_id"] != org_id:
            raise NotFoundError("Integration not found")
        item["last_synced_at"] = utc_now()
        item["updated_at"] = utc_now()
        result = IntegrationSyncResult(
            provider=item["provider"],
            status="success",
            synced_records=0,
            errors=0,
            started_at=item["last_synced_at"],
            finished_at=utc_now(),
        )
        return result

