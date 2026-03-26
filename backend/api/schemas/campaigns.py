from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common import PaginatedResponse


class SequenceResponse(BaseModel):
    id: str
    campaign_id: str
    lead_id: str | None = None
    variation_rank: int
    subject: str
    body: str
    hook_type: str | None = None
    confidence: float = 0.0
    status: str = "pending_approval"
    created_at: datetime


class CampaignCreate(BaseModel):
    name: str
    tone: str = "professional"
    product_value_prop: str | None = None
    brand_voice: str | None = None
    target_icp: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CampaignUpdate(BaseModel):
    name: str | None = None
    tone: str | None = None
    product_value_prop: str | None = None
    brand_voice: str | None = None
    target_icp: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class CampaignResponse(CampaignCreate):
    id: str
    org_id: str
    active: bool = True
    sequences: list[SequenceResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CampaignListResponse(PaginatedResponse[CampaignResponse]):
    pass

