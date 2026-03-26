from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base_repository import BaseRepository
from backend.db.models import Campaign, EmailSequence


class CampaignRepository(BaseRepository[Campaign]):
    model = Campaign

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Campaign)

    async def list_active(self, *, org_id: UUID) -> list[Campaign]:
        result = await self.session.execute(
            select(Campaign).where(Campaign.org_id == org_id, Campaign.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def list_matching_campaigns(self, *, org_id: UUID, filters: dict[str, object] | None = None) -> list[Campaign]:
        stmt = select(Campaign).where(Campaign.org_id == org_id, Campaign.is_active.is_(True))
        for key, value in (filters or {}).items():
            if value is not None and hasattr(Campaign, key):
                stmt = stmt.where(getattr(Campaign, key) == value)
        result = await self.session.execute(stmt.order_by(Campaign.updated_at.desc()))
        return list(result.scalars().all())

    async def create_sequence(self, *, org_id: UUID, data: dict[str, object]) -> EmailSequence:
        sequence = EmailSequence(org_id=org_id, **data)
        self.session.add(sequence)
        await self.session.flush()
        return sequence
