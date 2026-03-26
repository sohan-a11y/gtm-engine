from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base_repository import BaseRepository
from backend.db.models import Integration


class IntegrationRepository(BaseRepository[Integration]):
    model = Integration

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Integration)

    async def get_by_provider(self, *, org_id: UUID, provider: str) -> Integration | None:
        result = await self.session.execute(
            select(Integration).where(Integration.org_id == org_id, Integration.provider == provider)
        )
        return result.scalar_one_or_none()

    async def set_status(self, *, org_id: UUID, provider: str, status: str) -> Integration | None:
        record = await self.get_by_provider(org_id=org_id, provider=provider)
        if record is None:
            return None
        record.status = status
        return record
