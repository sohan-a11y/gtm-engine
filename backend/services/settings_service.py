from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.settings import OrgSettings
from backend.db.models import AgentConfiguration

from .base import BaseService

_ORG_SETTINGS_KEY = "_org_settings"


@dataclass(slots=True)
class SettingsService(BaseService):
    async def get_settings(self, org_id: str, *, session: AsyncSession) -> OrgSettings:
        row = await self._fetch_row(org_id, _ORG_SETTINGS_KEY, session)
        if row is None:
            return OrgSettings()
        return OrgSettings.model_validate(row.config or {})

    async def update_settings(self, org_id: str, data: OrgSettings, *, session: AsyncSession) -> OrgSettings:
        await self._upsert_row(org_id, _ORG_SETTINGS_KEY, data.model_dump(), session)
        return data

    async def get_llm_config(self, org_id: str, *, session: AsyncSession) -> OrgSettings:
        return await self.get_settings(org_id, session=session)

    async def update_llm_config(self, org_id: str, data: OrgSettings, *, session: AsyncSession) -> OrgSettings:
        return await self.update_settings(org_id, data, session=session)

    async def get_brand_voice(self, org_id: str, *, session: AsyncSession) -> OrgSettings:
        return await self.get_settings(org_id, session=session)

    async def update_brand_voice(self, org_id: str, data: OrgSettings, *, session: AsyncSession) -> OrgSettings:
        return await self.update_settings(org_id, data, session=session)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    async def _fetch_row(
        self, org_id: str, agent_name: str, session: AsyncSession
    ) -> AgentConfiguration | None:
        result = await session.execute(
            select(AgentConfiguration).where(
                AgentConfiguration.org_id == UUID(org_id),
                AgentConfiguration.agent_name == agent_name,
            )
        )
        return result.scalar_one_or_none()

    async def _upsert_row(
        self, org_id: str, agent_name: str, config: dict, session: AsyncSession
    ) -> AgentConfiguration:
        row = await self._fetch_row(org_id, agent_name, session)
        if row is None:
            row = AgentConfiguration(
                org_id=UUID(org_id),
                agent_name=agent_name,
                config=config,
            )
            session.add(row)
        else:
            row.config = config
        await session.commit()
        await session.refresh(row)
        return row
