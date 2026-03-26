from __future__ import annotations

from dataclasses import dataclass

from backend.api.schemas.deals import DealCreate, DealResponse, DealUpdate
from backend.core.exceptions import NotFoundError

from .base import BaseService
from .state import generate_id, utc_now


@dataclass(slots=True)
class DealService(BaseService):
    async def create_deal(self, org_id: str, data: DealCreate) -> DealResponse:
        deal_id = generate_id("deal")
        now = utc_now()
        record = {"id": deal_id, "org_id": org_id, "created_at": now, "updated_at": now, **data.model_dump()}
        self.state.deals[deal_id] = record
        return DealResponse.model_validate(record)

    async def list_deals(self, org_id: str) -> list[DealResponse]:
        return [
            DealResponse.model_validate(deal)
            for deal in self.state.deals.values()
            if deal["org_id"] == org_id
        ]

    async def get_deal(self, org_id: str, deal_id: str) -> DealResponse:
        deal = self.state.deals.get(deal_id)
        if not deal or deal["org_id"] != org_id:
            raise NotFoundError("Deal not found")
        return DealResponse.model_validate(deal)

    async def update_deal(self, org_id: str, deal_id: str, data: DealUpdate) -> DealResponse:
        deal = self.state.deals.get(deal_id)
        if not deal or deal["org_id"] != org_id:
            raise NotFoundError("Deal not found")
        deal.update(data.model_dump(exclude_none=True))
        deal["updated_at"] = utc_now()
        return DealResponse.model_validate(deal)

    async def analyze_risk(self, org_id: str, deal_id: str) -> DealResponse:
        deal = await self.get_deal(org_id, deal_id)
        stored = self.state.deals[deal_id]
        amount = float(stored.get("amount") or 0)
        stage = stored.get("stage", "")
        risk = 0.25
        if amount > 100_000:
            risk += 0.25
        if stage in {"negotiation", "contracting", "closed_lost"}:
            risk += 0.25
        stored["risk_score"] = min(1.0, round(risk, 3))
        stored["updated_at"] = utc_now()
        return DealResponse.model_validate(stored)

