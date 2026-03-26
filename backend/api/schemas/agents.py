from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentActionRequest(BaseModel):
    org_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentActionResponse(BaseModel):
    agent_name: str
    status: str
    result: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    id: str
    agent_name: str
    org_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

