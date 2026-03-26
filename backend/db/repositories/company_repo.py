from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base_repository import BaseRepository
from backend.db.models import Company


class CompanyRepository(BaseRepository[Company]):
    model = Company

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Company)

    async def get_by_domain(self, *, org_id: UUID, domain: str) -> Company | None:
        result = await self.session.execute(
            select(Company).where(Company.org_id == org_id, Company.domain == domain)
        )
        return result.scalar_one_or_none()

    async def list_with_health_score(
        self, *, org_id: UUID, minimum_score: float | None = None, limit: int = 100
    ) -> list[Company]:
        stmt = select(Company).where(Company.org_id == org_id)
        if minimum_score is not None:
            stmt = stmt.where(Company.health_score >= minimum_score)
        result = await self.session.execute(stmt.order_by(Company.health_score.desc().nullslast()).limit(limit))
        return list(result.scalars().all())
