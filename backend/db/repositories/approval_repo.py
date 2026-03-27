from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import EmailSequence


class ApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_pending(self, *, org_id: UUID, limit: int = 100, offset: int = 0) -> list[EmailSequence]:
        result = await self.session.execute(
            select(EmailSequence)
            .where(EmailSequence.org_id == org_id)
            .order_by(EmailSequence.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get(self, *, org_id: UUID, approval_id: UUID) -> EmailSequence | None:
        result = await self.session.execute(
            select(EmailSequence).where(
                EmailSequence.org_id == org_id,
                EmailSequence.id == approval_id,
            )
        )
        return result.scalar_one_or_none()

    async def set_status(
        self,
        *,
        org_id: UUID,
        approval_id: UUID,
        status: str,
        reviewer_id: UUID | None = None,
    ) -> EmailSequence | None:
        from backend.db.models import utc_now as _now
        seq = await self.get(org_id=org_id, approval_id=approval_id)
        if seq is None:
            return None
        seq.status = status
        if reviewer_id is not None:
            seq.approved_by_user_id = reviewer_id
            seq.approved_at = _now()
        return seq
