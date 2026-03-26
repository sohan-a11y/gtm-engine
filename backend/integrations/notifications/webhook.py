from __future__ import annotations

from typing import Any


class GenericWebhookClient:
    provider_name = "webhook"

    def __init__(self, *, endpoint_url: str | None = None, secret: str | None = None) -> None:
        self.endpoint_url = endpoint_url
        self.secret = secret

    async def post_event(self, *, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "event_type": event_type,
            "payload": payload,
            "status": "queued",
        }
