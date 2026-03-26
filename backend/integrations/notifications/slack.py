from __future__ import annotations

from typing import Any


class SlackWebhookClient:
    provider_name = "slack"

    def __init__(self, *, webhook_url: str | None = None, channel: str | None = None) -> None:
        self.webhook_url = webhook_url
        self.channel = channel

    async def send_message(self, *, text: str, channel: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "channel": channel or self.channel,
            "text": text,
            "metadata": metadata or {},
            "status": "queued",
        }
