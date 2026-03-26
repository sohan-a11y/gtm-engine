from __future__ import annotations

from dataclasses import dataclass

from backend.api.schemas.settings import OrgSettings

from .base import BaseService


@dataclass(slots=True)
class SettingsService(BaseService):
    async def get_settings(self, org_id: str) -> OrgSettings:
        return OrgSettings.model_validate(self.state.settings.get(org_id) or {})

    async def update_settings(self, org_id: str, data: OrgSettings) -> OrgSettings:
        self.state.settings[org_id] = data.model_dump()
        return OrgSettings.model_validate(self.state.settings[org_id])

