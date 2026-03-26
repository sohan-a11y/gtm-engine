from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common import PaginatedResponse


class DealCreate(BaseModel):
    name: str
    company_id: str | None = None
    amount: float | None = None
    stage: str = "prospecting"
    risk_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DealUpdate(BaseModel):
    name: str | None = None
    company_id: str | None = None
    amount: float | None = None
    stage: str | None = None
    risk_score: float | None = None
    metadata: dict[str, Any] | None = None


class DealResponse(DealCreate):
    id: str
    org_id: str
    created_at: datetime
    updated_at: datetime


class DealListResponse(PaginatedResponse[DealResponse]):
    pass

