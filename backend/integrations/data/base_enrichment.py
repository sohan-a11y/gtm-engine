from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseEnrichmentClient(ABC):
    provider_name = "enrichment"

    @abstractmethod
    async def enrich_contact(self, *, contact: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def verify_email(self, *, email: str) -> dict[str, Any]:
        raise NotImplementedError
