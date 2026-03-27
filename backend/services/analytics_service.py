from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.analytics import AnalyticsOverview, OutboundMetrics, PipelineMetrics, RetentionMetrics
from backend.core.exceptions import ServiceUnavailableError
from backend.db.models import Campaign, Contact, Deal, EmailSequence

from .base import BaseService

_CLOSED_WON = "closed_won"
_CLOSED_LOST = "closed_lost"
_CLOSED = (_CLOSED_WON, _CLOSED_LOST)


@dataclass(slots=True)
class AnalyticsService(BaseService):
    async def get_overview(self, org_id: str, *, session: AsyncSession) -> AnalyticsOverview:
        try:
            return await _compute_overview(org_id, session)
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc

    async def get_summary(self, org_id: str, *, session: AsyncSession) -> dict:
        """Flat summary dict consumed by the frontend /analytics/summary endpoint."""
        try:
            overview = await _compute_overview(org_id, session)
            pipeline_value = await _pipeline_value(org_id, session)
            active_cams = await _active_campaigns(org_id, session)
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc

        return {
            "leads_scored": overview.ai_usage.get("leads_scored", 0),
            "emails_generated": overview.outbound.drafts_created,
            "emails_approved": overview.outbound.approved,
            "active_campaigns": active_cams,
            "pipeline_value": pipeline_value,
            "churn_at_risk": overview.retention.at_risk_accounts,
            "pipeline": overview.pipeline.model_dump(),
            "outbound": overview.outbound.model_dump(),
            "retention": overview.retention.model_dump(),
            "ai_usage": overview.ai_usage,
        }


async def _compute_overview(org_id: str, session: AsyncSession) -> AnalyticsOverview:
    uuid = UUID(org_id)

    # ── pipeline ──────────────────────────────────────────────────────────────
    deal_stages = (await session.execute(
        select(Deal.stage).where(Deal.org_id == uuid)
    )).scalars().all()

    open_deals = sum(1 for s in deal_stages if s not in _CLOSED)
    won_deals = sum(1 for s in deal_stages if s == _CLOSED_WON)
    lost_deals = sum(1 for s in deal_stages if s == _CLOSED_LOST)

    total_leads = (await session.execute(
        select(func.count()).select_from(Contact).where(Contact.org_id == uuid)
    )).scalar_one()
    qualified = (await session.execute(
        select(func.count()).select_from(Contact).where(
            Contact.org_id == uuid, Contact.status == "qualified"
        )
    )).scalar_one()
    conversion_rate = round(qualified / max(total_leads, 1), 3)

    pipeline = PipelineMetrics(
        open_deals=open_deals,
        won_deals=won_deals,
        lost_deals=lost_deals,
        conversion_rate=conversion_rate,
    )

    # ── outbound ──────────────────────────────────────────────────────────────
    drafts = (await session.execute(
        select(func.count()).select_from(EmailSequence).where(EmailSequence.org_id == uuid)
    )).scalar_one()
    approved = (await session.execute(
        select(func.count()).select_from(EmailSequence).where(
            EmailSequence.org_id == uuid, EmailSequence.status == "approved"
        )
    )).scalar_one()
    sent = (await session.execute(
        select(func.count()).select_from(EmailSequence).where(
            EmailSequence.org_id == uuid, EmailSequence.status == "sent"
        )
    )).scalar_one()

    outbound = OutboundMetrics(
        drafts_created=drafts,
        approved=approved,
        sent=sent,
        reply_rate=0.0,
    )

    # ── retention ─────────────────────────────────────────────────────────────
    risk_scores = (await session.execute(
        select(Deal.risk_score).where(Deal.org_id == uuid, Deal.risk_score.isnot(None))
    )).scalars().all()

    at_risk = sum(1 for r in risk_scores if r and r > 0.75)
    _churn_sum: float = sum(r for r in risk_scores if r)
    avg_churn: float = round(_churn_sum / max(len(risk_scores), 1), 3)  # type: ignore[call-overload]
    expansion = (await session.execute(
        select(func.count()).select_from(Contact).where(
            Contact.org_id == uuid, Contact.icp_score > 0.8
        )
    )).scalar_one()

    retention = RetentionMetrics(
        at_risk_accounts=at_risk,
        churn_risk=avg_churn,
        expansion_opportunities=expansion,
    )

    # ── AI usage ──────────────────────────────────────────────────────────────
    scored = (await session.execute(
        select(func.count()).select_from(Contact).where(
            Contact.org_id == uuid, Contact.icp_score.isnot(None)
        )
    )).scalar_one()

    return AnalyticsOverview(
        pipeline=pipeline,
        outbound=outbound,
        retention=retention,
        ai_usage={"leads_scored": float(scored)},
    )


async def _pipeline_value(org_id: str, session: AsyncSession) -> float:
    uuid = UUID(org_id)
    total = (await session.execute(
        select(func.coalesce(func.sum(Deal.amount_cents), 0)).where(
            Deal.org_id == uuid, Deal.stage.notin_(_CLOSED)
        )
    )).scalar_one()
    return round(float(total or 0) / 100, 2)  # type: ignore[call-overload]


async def _active_campaigns(org_id: str, session: AsyncSession) -> int:
    uuid = UUID(org_id)
    return (await session.execute(
        select(func.count()).select_from(Campaign).where(
            Campaign.org_id == uuid, Campaign.status == "active"
        )
    )).scalar_one()
