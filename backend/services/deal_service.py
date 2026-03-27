from __future__ import annotations

import logging
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.deal_intel_agent import DealIntelAgent
from backend.api.schemas.deals import DealCreate, DealResponse, DealUpdate
from backend.core.exceptions import NotFoundError, ServiceUnavailableError
from backend.enrichment.transcript_parser import TranscriptInsight
from backend.core.llm_router import LLMRouter, build_llm_router
from backend.db.models import Deal
from backend.db.repositories.deal_repo import DealRepository

from .base import BaseService

logger = logging.getLogger(__name__)


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
    llm_router: LLMRouter = field(default_factory=build_llm_router)

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

        try:
            agent = DealIntelAgent(llm_router=self.llm_router)
            context = {
                "name": deal.name,
                "stage": deal.stage,
                "amount": deal.amount_cents / 100 if deal.amount_cents else 0,
                "risk_score": deal.risk_score,
            }
            result = await agent.analyze(deal=context)
            deal.risk_score = result.risk_score
            deal.risk_level = result.risk_level
            deal.risk_factors = result.risk_factors
            deal.positive_signals = result.positive_signals
            deal.recommended_actions = result.recommended_actions
            deal.deal_summary = result.deal_summary
            if result.likely_close_date is not None:
                deal.likely_close_date = result.likely_close_date
        except Exception:
            logger.exception("DealIntelAgent failed for deal %s; falling back to heuristic", deal_id)
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

    async def attach_transcript(
        self, deal_id: str, insight: TranscriptInsight, *, session: AsyncSession
    ) -> DealResponse:
        result = await session.execute(select(Deal).where(Deal.id == UUID(deal_id)))
        deal = result.scalar_one_or_none()
        if deal is None:
            raise NotFoundError("Deal not found")
        existing_notes: str = getattr(deal, "notes", "") or ""
        deal.notes = (existing_notes + "\n\n" + insight.summary).strip()  # type: ignore[attr-defined]
        try:
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return _deal_to_response(deal)
