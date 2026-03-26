from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base_repository import BaseRepository
from backend.db.models import Contact


class ContactRepository(BaseRepository[Contact]):
    model = Contact

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Contact)

    async def get_by_email(self, *, org_id: UUID, email: str) -> Contact | None:
        result = await self.session.execute(
            select(Contact).where(Contact.org_id == org_id, Contact.email == email)
        )
        return result.scalar_one_or_none()

    async def list_ready_for_scoring(self, *, org_id: UUID, limit: int = 100) -> list[Contact]:
        result = await self.session.execute(
            select(Contact)
            .where(Contact.org_id == org_id, Contact.status.in_(["new", "enriched"]))
            .order_by(Contact.last_enriched_at.is_(None).desc(), Contact.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_enriched(self, *, org_id: UUID, contact_id: UUID, enrichment_data: dict) -> Contact | None:
        contact = await self.get(org_id=org_id, object_id=contact_id)
        if contact is None:
            return None
        contact.enrichment_data = enrichment_data
        contact.enrichment_status = "enriched"
        return contact

    async def mark_scored(
        self,
        *,
        org_id: UUID,
        contact_id: UUID,
        score: float | None,
        reason: str | None,
        fit_signals: list[str],
        gap_signals: list[str],
        embedding: list[float] | None = None,
    ) -> Contact | None:
        contact = await self.get(org_id=org_id, object_id=contact_id)
        if contact is None:
            return None
        contact.icp_score = score
        contact.icp_score_reason = reason
        contact.fit_signals = fit_signals
        contact.gap_signals = gap_signals
        contact.embedding = embedding
        return contact
