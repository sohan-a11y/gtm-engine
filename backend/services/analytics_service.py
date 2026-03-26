from __future__ import annotations

from dataclasses import dataclass

from backend.api.schemas.analytics import AnalyticsOverview, OutboundMetrics, PipelineMetrics, RetentionMetrics

from .base import BaseService


@dataclass(slots=True)
class AnalyticsService(BaseService):
    async def get_overview(self, org_id: str) -> AnalyticsOverview:
        leads = [lead for lead in self.state.leads.values() if lead["org_id"] == org_id]
        deals = [deal for deal in self.state.deals.values() if deal["org_id"] == org_id]
        campaigns = [campaign for campaign in self.state.campaigns.values() if campaign["org_id"] == org_id]
        approvals = [item for item in self.state.approvals.values() if item["org_id"] == org_id]
        pipeline = PipelineMetrics(
            open_deals=len([deal for deal in deals if deal.get("stage") not in {"closed_won", "closed_lost"}]),
            won_deals=len([deal for deal in deals if deal.get("stage") == "closed_won"]),
            lost_deals=len([deal for deal in deals if deal.get("stage") == "closed_lost"]),
            conversion_rate=round(len([lead for lead in leads if lead.get("status") == "qualified"]) / max(len(leads), 1), 3),
        )
        outbound = OutboundMetrics(
            drafts_created=sum(len(campaign.get("sequences", [])) for campaign in campaigns),
            approved=len([item for item in approvals if item.get("status") == "approved"]),
            sent=len([item for item in approvals if item.get("status") == "sent"]),
            reply_rate=0.0,
        )
        retention = RetentionMetrics(
            at_risk_accounts=len([deal for deal in deals if float(deal.get("risk_score") or 0) > 0.75]),
            churn_risk=round(
                sum(float(deal.get("risk_score") or 0) for deal in deals) / max(len(deals), 1), 3
            ),
            expansion_opportunities=len([lead for lead in leads if float(lead.get("icp_score") or 0) > 0.8]),
        )
        return AnalyticsOverview(
            pipeline=pipeline,
            outbound=outbound,
            retention=retention,
            ai_usage={"lead_scored": float(len([lead for lead in leads if lead.get("icp_score") is not None]))},
        )

