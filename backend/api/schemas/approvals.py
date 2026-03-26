from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common import PaginatedResponse


class ApprovalItem(BaseModel):
    id: str
    org_id: str
    target_type: str
    target_id: str
    title: str
    body: str
    status: str = "pending"
    reviewer_id: str | None = None
    reviewed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ApprovalActionRequest(BaseModel):
    note: str | None = None


class ApprovalListResponse(PaginatedResponse[ApprovalItem]):
    pass
