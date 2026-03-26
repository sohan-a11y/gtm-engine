from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


@dataclass(slots=True)
class ServiceState:
    users: dict[str, dict[str, Any]] = field(default_factory=dict)
    orgs: dict[str, dict[str, Any]] = field(default_factory=dict)
    leads: dict[str, dict[str, Any]] = field(default_factory=dict)
    companies: dict[str, dict[str, Any]] = field(default_factory=dict)
    deals: dict[str, dict[str, Any]] = field(default_factory=dict)
    campaigns: dict[str, dict[str, Any]] = field(default_factory=dict)
    approvals: dict[str, dict[str, Any]] = field(default_factory=dict)
    integrations: dict[str, dict[str, Any]] = field(default_factory=dict)
    settings: dict[str, dict[str, Any]] = field(default_factory=dict)
    audit_log: list[dict[str, Any]] = field(default_factory=list)
    jobs: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: asyncio.Queue[dict[str, Any]] = field(default_factory=asyncio.Queue)

    def publish_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.put_nowait(
            {
                "type": event_type,
                "timestamp": utc_now().isoformat(),
                "payload": payload,
            }
        )


STATE = ServiceState()


def get_state() -> ServiceState:
    return STATE

