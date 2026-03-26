from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base_repository import BaseRepository
from backend.db.models import Deal


class DealRepository(BaseRepository[Deal]):
    model = Deal

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Deal)

    async def list_pipeline(self, *, org_id: UUID, stage: str | None = None) -> list[Deal]:
        stmt = select(Deal).where(Deal.org_id == org_id)
        if stage:
            stmt = stmt.where(Deal.stage == stage)
        result = await self.session.execute(stmt.order_by(Deal.days_in_stage.desc()))
        return list(result.scalars().all())
