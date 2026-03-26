from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseCRM(ABC):
    provider_name = "crm"

    @abstractmethod
    async def get_contacts(self, *, cursor: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def get_companies(self, *, cursor: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def get_deals(self, *, cursor: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def update_contact(self, *, external_id: str, data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def create_activity(self, *, external_contact_id: str, data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
