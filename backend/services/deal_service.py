from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.deals import DealCreate, DealResponse, DealUpdate
from backend.core.exceptions import NotFoundError, ServiceUnavailableError
from backend.db.models import Deal
from backend.db.repositories.deal_repo import DealRepository

from .base import BaseService


def _deal_to_response(deal: Deal) -> DealResponse:
    return DealResponse(
        id=str(deal.id),
        org_id=str(deal.org_id),
        name=deal.name,
        company_id=str(deal.company_id) if deal.company_id else None,
        amount=deal.amount_cents / 100 if deal.amount_cents else None,
        stage=deal.stage,
        risk_score=deal.risk_score,
        metadata={},
        created_at=deal.created_at,
        updated_at=deal.updated_at,
    )


@dataclass(slots=True)
class DealService(BaseService):
    async def create_deal(self, org_id: str, data: DealCreate, *, session: AsyncSession) -> DealResponse:
        repo = DealRepository(session)
        payload = {
            "name": data.name,
            "company_id": UUID(data.company_id) if data.company_id else None,
            "amount_cents": int((data.amount or 0) * 100),
            "stage": data.stage,
            "risk_score": data.risk_score,
        }
        try:
            deal = await repo.create(org_id=UUID(org_id), data=payload)
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return _deal_to_response(deal)

    async def list_deals(self, org_id: str, *, session: AsyncSession) -> list[DealResponse]:
        repo = DealRepository(session)
        try:
            deals = await repo.list(org_id=UUID(org_id))
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return [_deal_to_response(d) for d in deals]

    async def get_deal(self, org_id: str, deal_id: str, *, session: AsyncSession) -> DealResponse:
        repo = DealRepository(session)
        try:
            deal = await repo.get(org_id=UUID(org_id), object_id=UUID(deal_id))
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if deal is None:
            raise NotFoundError("Deal not found")
        return _deal_to_response(deal)

    async def update_deal(self, org_id: str, deal_id: str, data: DealUpdate, *, session: AsyncSession) -> DealResponse:
        repo = DealRepository(session)
        updates = data.model_dump(exclude_none=True)
        # Convert amount (dollars) → amount_cents
        if "amount" in updates:
            updates["amount_cents"] = int((updates.pop("amount") or 0) * 100)
        # company_id string → UUID
        if "company_id" in updates and updates["company_id"] is not None:
            updates["company_id"] = UUID(updates["company_id"])
        # Drop schema-only fields not in model
        updates.pop("metadata", None)
        try:
            deal = await repo.update_by_id(org_id=UUID(org_id), object_id=UUID(deal_id), data=updates)
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if deal is None:
            raise NotFoundError("Deal not found")
        return _deal_to_response(deal)

    async def analyze_risk(self, org_id: str, deal_id: str, *, session: AsyncSession) -> DealResponse:
        repo = DealRepository(session)
        try:
            deal = await repo.get(org_id=UUID(org_id), object_id=UUID(deal_id))
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if deal is None:
            raise NotFoundError("Deal not found")
        amount = (deal.amount_cents or 0) / 100
        stage = deal.stage or ""
        risk = 0.25
        if amount > 100_000:
            risk += 0.25
        if stage in {"negotiation", "contracting", "closed_lost"}:
            risk += 0.25
        deal.risk_score = min(1.0, round(risk, 3))
        try:
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return _deal_to_response(deal)
