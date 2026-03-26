from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common import PaginatedResponse


class IntegrationConnectRequest(BaseModel):
    provider: str
    credentials: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntegrationSyncResult(BaseModel):
    provider: str
    status: str
    synced_records: int = 0
    errors: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None


class IntegrationResponse(BaseModel):
    id: str
    org_id: str
    provider: str
    status: str = "connected"
    credentials: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class IntegrationListResponse(PaginatedResponse[IntegrationResponse]):
    pass

