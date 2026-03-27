from __future__ import annotations

from typing import Any

import httpx


class SlackWebhookClient:
    provider_name = "slack"

    def __init__(self, *, webhook_url: str | None = None, channel: str | None = None) -> None:
        self.webhook_url = webhook_url
        self.channel = channel

    async def send_message(self, *, text: str, channel: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.webhook_url:
            return {
                "provider": self.provider_name,
                "channel": channel or self.channel,
                "text": text,
                "metadata": metadata or {},
                "status": "queued",
            }
        blocks = (metadata or {}).get("blocks") if metadata else None
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                self.webhook_url,
                json={"text": text, "blocks": blocks} if blocks else {"text": text},
            )
            resp.raise_for_status()
        return {"status": "sent", "provider": "slack"}
