from __future__ import annotations

import asyncio
import json
import os
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from backend.api.dependencies import get_current_user, CurrentUser

router = APIRouter(tags=["events"])

_HEARTBEAT_INTERVAL = int(os.getenv("SSE_HEARTBEAT_SECONDS", "30"))
_CHANNEL_PREFIX = "gtm:events"


def _channel(org_id: str) -> str:
    return f"{_CHANNEL_PREFIX}:{org_id}"


async def _redis_event_stream(org_id: str, request: Request) -> AsyncGenerator[str, None]:
    """
    Subscribe to the Redis Pub/Sub channel for this org and stream events as
    SSE.  Falls back to the in-process asyncio queue when Redis is unavailable
    (e.g. local dev without Redis).
    """
    yield ": connected\n\n"

    redis_client = None
    pubsub = None

    # Try to acquire a Redis connection from the app state.
    try:
        redis_client = getattr(request.app.state, "redis", None)
        if redis_client is not None:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(_channel(org_id))
    except Exception:
        redis_client = None
        pubsub = None

    if pubsub is not None:
        # ── Redis-backed path (multi-worker safe) ─────────────────────────
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=_HEARTBEAT_INTERVAL,
                    )
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
                    continue

                if message and message.get("type") == "message":
                    try:
                        event = json.loads(message["data"])
                        yield f"event: {event.get('type', 'message')}\n"
                        yield f"data: {json.dumps(event)}\n\n"
                    except (json.JSONDecodeError, TypeError):
                        pass
        finally:
            try:
                await pubsub.unsubscribe(_channel(org_id))
                await pubsub.close()
            except Exception:
                pass
    else:
        # ── Fallback: local asyncio queue (single-worker / dev mode) ──────
        from backend.services.state import get_state
        state = get_state()
        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(state.events.get(), timeout=_HEARTBEAT_INTERVAL)
                yield f"event: {event.get('type', 'message')}\n"
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"


@router.get("/events/agent-status")
async def agent_status_events(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    """
    Server-Sent Events stream for real-time agent status updates.

    Events are scoped to the authenticated user's org.  The stream stays open
    indefinitely; a heartbeat comment is sent every 30 s to keep the connection
    alive through proxies.

    Nginx must be configured with ``proxy_buffering off`` and
    ``X-Accel-Buffering: no`` for this endpoint.
    """
    return StreamingResponse(
        _redis_event_stream(current_user.org_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


async def publish_event(redis_client, org_id: str, event_type: str, payload: dict) -> None:
    """
    Publish an event to the org-scoped Redis channel.

    Call this from services/workers after any significant state change
    (enrichment complete, scoring complete, outbound draft ready, etc.).

    Falls back silently when Redis is unavailable so the main workflow is
    never blocked by an SSE publish failure.
    """
    event = {"type": event_type, **payload}
    try:
        if redis_client is not None:
            await redis_client.publish(_channel(org_id), json.dumps(event))
        else:
            from backend.services.state import get_state
            get_state().publish_event(event_type, payload)
    except Exception:
        pass
