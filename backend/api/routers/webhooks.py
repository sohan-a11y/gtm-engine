from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

from fastapi import APIRouter, Header, Request

from backend.core.exceptions import AuthenticationError
from backend.services import integration_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_signature(body: bytes, signature: str | None) -> None:
    secret = os.getenv("WEBHOOK_SECRET")
    if not secret:
        return
    if not signature:
        raise AuthenticationError("Missing webhook signature")
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise AuthenticationError("Invalid webhook signature")


async def _handle_webhook(source: str, request: Request, signature: str | None) -> dict[str, Any]:
    body = await request.body()
    _verify_signature(body, signature)
    integration_service.state.publish_event("webhook_received", {"source": source, "body": body.decode("utf-8")})
    return {"status": "accepted", "source": source}


@router.post("/hubspot")
async def hubspot_webhook(request: Request, x_hubspot_signature: str | None = Header(default=None)) -> dict[str, Any]:
    return await _handle_webhook("hubspot", request, x_hubspot_signature)


@router.post("/salesforce")
async def salesforce_webhook(request: Request, x_salesforce_signature: str | None = Header(default=None)) -> dict[str, Any]:
    return await _handle_webhook("salesforce", request, x_salesforce_signature)

