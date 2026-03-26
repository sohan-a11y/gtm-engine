from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common import PaginatedResponse


class CompanyCreate(BaseModel):
    name: str
    domain: str | None = None
    industry: str | None = None
    employee_count: int | None = None
    health_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompanyUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    industry: str | None = None
    employee_count: int | None = None
    health_score: float | None = None
    metadata: dict[str, Any] | None = None


class CompanyResponse(CompanyCreate):
    id: str
    org_id: str
    created_at: datetime
    updated_at: datetime


class CompanyListResponse(PaginatedResponse[CompanyResponse]):
    pass

