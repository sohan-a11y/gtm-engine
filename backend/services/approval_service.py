from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.approvals import ApprovalActionRequest, ApprovalItem
from backend.core.exceptions import NotFoundError, ServiceUnavailableError
from backend.db.models import EmailSequence
from backend.db.repositories.approval_repo import ApprovalRepository

from .base import BaseService


def _seq_to_approval(seq: EmailSequence) -> ApprovalItem:
    return ApprovalItem(
        id=str(seq.id),
        org_id=str(seq.org_id),
        target_type="email_sequence",
        target_id=str(seq.id),
        title=seq.subject,
        body=seq.body,
        status=seq.status,
        reviewer_id=str(seq.approved_by_user_id) if seq.approved_by_user_id else None,
        reviewed_at=seq.approved_at,
        metadata=seq.metadata_json or {},
        created_at=seq.created_at,
        updated_at=seq.updated_at,
    )


@dataclass(slots=True)
class ApprovalService(BaseService):
    async def list_approvals(self, org_id: str, *, session: AsyncSession) -> list[ApprovalItem]:
        repo = ApprovalRepository(session)
        try:
            seqs = await repo.list_pending(org_id=UUID(org_id))
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return [_seq_to_approval(s) for s in seqs]

    async def get_approval(self, org_id: str, approval_id: str, *, session: AsyncSession) -> ApprovalItem:
        repo = ApprovalRepository(session)
        try:
            seq = await repo.get(org_id=UUID(org_id), approval_id=UUID(approval_id))
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if seq is None:
            raise NotFoundError("Approval not found")
        return _seq_to_approval(seq)

    async def approve(
        self,
        org_id: str,
        approval_id: str,
        reviewer_id: str,
        request: ApprovalActionRequest,
        *,
        session: AsyncSession,
    ) -> ApprovalItem:
        repo = ApprovalRepository(session)
        try:
            seq = await repo.set_status(
                org_id=UUID(org_id),
                approval_id=UUID(approval_id),
                status="approved",
                reviewer_id=UUID(reviewer_id),
            )
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if seq is None:
            raise NotFoundError("Approval not found")
        meta = dict(seq.metadata_json or {})
        if request.note is not None:
            meta["note"] = request.note
        seq.metadata_json = meta
        try:
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return _seq_to_approval(seq)

    async def reject(
        self,
        org_id: str,
        approval_id: str,
        reviewer_id: str,
        request: ApprovalActionRequest,
        *,
        session: AsyncSession,
    ) -> ApprovalItem:
        repo = ApprovalRepository(session)
        try:
            seq = await repo.set_status(
                org_id=UUID(org_id),
                approval_id=UUID(approval_id),
                status="rejected",
                reviewer_id=UUID(reviewer_id),
            )
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if seq is None:
            raise NotFoundError("Approval not found")
        meta = dict(seq.metadata_json or {})
        if request.note is not None:
            meta["note"] = request.note
        seq.metadata_json = meta
        try:
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return _seq_to_approval(seq)

    async def mark_replied(
        self,
        org_id: str,
        approval_id: str,
        *,
        session: AsyncSession,
    ) -> ApprovalItem:
        repo = ApprovalRepository(session)
        try:
            seq = await repo.set_status(
                org_id=UUID(org_id),
                approval_id=UUID(approval_id),
                status="replied",
            )
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if seq is None:
            raise NotFoundError("Approval not found")
        try:
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return _seq_to_approval(seq)
