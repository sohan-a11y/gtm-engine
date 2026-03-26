from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MetricPoint(BaseModel):
    timestamp: datetime
    value: float
    label: str | None = None


class PipelineMetrics(BaseModel):
    open_deals: int = 0
    won_deals: int = 0
    lost_deals: int = 0
    conversion_rate: float = 0.0
    series: list[MetricPoint] = Field(default_factory=list)


class OutboundMetrics(BaseModel):
    drafts_created: int = 0
    approved: int = 0
    sent: int = 0
    reply_rate: float = 0.0


class RetentionMetrics(BaseModel):
    at_risk_accounts: int = 0
    churn_risk: float = 0.0
    expansion_opportunities: int = 0


class AnalyticsOverview(BaseModel):
    pipeline: PipelineMetrics = Field(default_factory=PipelineMetrics)
    outbound: OutboundMetrics = Field(default_factory=OutboundMetrics)
    retention: RetentionMetrics = Field(default_factory=RetentionMetrics)
    ai_usage: dict[str, float] = Field(default_factory=dict)

