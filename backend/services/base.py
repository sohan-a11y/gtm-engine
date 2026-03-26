from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .state import ServiceState, get_state, utc_now


@dataclass(slots=True)
class BaseService:
    state: ServiceState = field(default_factory=get_state)

    def _timestamp(self) -> str:
        return utc_now().isoformat()

    def _scope_items(self, items: dict[str, dict[str, Any]], org_id: str) -> list[dict[str, Any]]:
        return [item for item in items.values() if item.get("org_id") == org_id]

