from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseEmail(ABC):
    provider_name = "email"

    @abstractmethod
    async def send_email(self, *, to: str, subject: str, body: str, from_address: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def check_deliverability(self, *, email: str) -> dict[str, Any]:
        raise NotImplementedError
