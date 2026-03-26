from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from .common import PaginatedResponse


class LeadCreate(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    company_name: str | None = None
    title: str | None = None
    source: str = "manual"
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LeadUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    company_name: str | None = None
    title: str | None = None
    source: str | None = None
    status: str | None = None
    notes: str | None = None
    icp_score: float | None = None
    enrichment_status: str | None = None
    enrichment_data: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class LeadResponse(LeadCreate):
    id: str
    org_id: str
    status: str = "new"
    icp_score: float | None = None
    icp_score_reason: str | None = None
    fit_signals: list[str] = Field(default_factory=list)
    gap_signals: list[str] = Field(default_factory=list)
    enrichment_status: str = "pending"
    enrichment_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class LeadListResponse(PaginatedResponse[LeadResponse]):
    pass


class LeadImportResult(BaseModel):
    imported: int
    skipped: int
    duplicates: int
    errors: int = 0

