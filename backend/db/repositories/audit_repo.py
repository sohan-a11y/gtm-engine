from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base_repository import BaseRepository
from backend.db.models import AgentAuditLog


class AuditRepository(BaseRepository[AgentAuditLog]):
    model = AgentAuditLog

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AgentAuditLog)

    async def append(self, *, org_id: UUID, data: dict[str, object]) -> AgentAuditLog:
        record = AgentAuditLog(org_id=org_id, **data)
        self.session.add(record)
        await self.session.flush()
        return record

    async def list_recent(self, *, org_id: UUID, limit: int = 100) -> list[AgentAuditLog]:
        result = await self.session.execute(
            select(AgentAuditLog)
            .where(AgentAuditLog.org_id == org_id)
            .order_by(desc(AgentAuditLog.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
