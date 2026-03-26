from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .logging_config import get_logger

audit_logger = get_logger("gtm.audit")


@dataclass(slots=True)
class AuditRecord:
    event_type: str
    org_id: str
    actor_id: str | None = None
    agent_name: str | None = None
    prompt: str | None = None
    response: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(slots=True)
class AuditLogger:
    records: list[AuditRecord] = field(default_factory=list)

    def append(self, record: AuditRecord) -> AuditRecord:
        self.records.append(record)
        audit_logger.info(
            json.dumps(
                {
                    "event_type": record.event_type,
                    "org_id": record.org_id,
                    "actor_id": record.actor_id,
                    "agent_name": record.agent_name,
                    "created_at": record.created_at,
                }
            )
        )
        return record

    def log_agent_run(
        self,
        *,
        org_id: str,
        agent_name: str,
        prompt: str,
        response: str,
        actor_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditRecord:
        return self.append(
            AuditRecord(
                event_type="agent_run",
                org_id=org_id,
                actor_id=actor_id,
                agent_name=agent_name,
                prompt=prompt,
                response=response,
                metadata=metadata or {},
            )
        )


def build_audit_logger() -> AuditLogger:
    return AuditLogger()

