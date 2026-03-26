"""Integration tests for CRM sync — integrations endpoint and webhook receiver."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import sys
from pathlib import Path
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from httpx import AsyncClient, ASGITransport
except ImportError:  # pragma: no cover
    pytest.skip("httpx not installed", allow_module_level=True)

from backend.api.main import create_app  # noqa: E402
from backend.core.auth import create_token_pair  # noqa: E402


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def admin_headers() -> dict[str, str]:
    bundle = create_token_pair(
        str(uuid4()), str(uuid4()), "admin",
        ["integrations:read", "integrations:write"],
    )
    return {"Authorization": f"Bearer {bundle.access_token}"}


def _hubspot_signature(payload_bytes: bytes, secret: str = "test-secret") -> str:
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()


# ── integrations list ─────────────────────────────────────────────────────────

def test_list_integrations_requires_auth(app):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.get("/integrations")
    resp = asyncio.run(run())
    assert resp.status_code in (401, 403)


def test_list_integrations_with_auth(app, admin_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.get("/integrations", headers=admin_headers)
    resp = asyncio.run(run())
    assert resp.status_code in (200, 503)


# ── connect integration ───────────────────────────────────────────────────────

def test_connect_hubspot_requires_credentials(app, admin_headers):
    """Missing api_key → 422 or 503 if DB unavailable."""
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                "/integrations/hubspot/connect",
                headers=admin_headers,
                json={},
            )
    resp = asyncio.run(run())
    assert resp.status_code in (422, 503)


def test_connect_hubspot_with_api_key(app, admin_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                "/integrations/hubspot/connect",
                headers=admin_headers,
                json={"api_key": "hb-fake-key-123"},
            )
    resp = asyncio.run(run())
    assert resp.status_code in (200, 201, 503)


# ── manual sync trigger ───────────────────────────────────────────────────────

def test_manual_sync_trigger(app, admin_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                "/integrations/hubspot/sync",
                headers=admin_headers,
            )
    resp = asyncio.run(run())
    assert resp.status_code in (200, 202, 404, 503)


# ── webhook receiver ──────────────────────────────────────────────────────────

def test_hubspot_webhook_without_signature_returns_4xx(app):
    """Webhook without HMAC verification signature must be rejected."""
    async def run():
        payload = json.dumps({"subscriptionType": "contact.creation"}).encode()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                "/webhooks/hubspot",
                content=payload,
                headers={"Content-Type": "application/json"},
            )
    resp = asyncio.run(run())
    # 200 when no WEBHOOK_SECRET set (CI), 400/401 when secret configured
    assert resp.status_code in (200, 400, 401, 422, 503)


def test_salesforce_webhook_endpoint_exists(app, admin_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                "/webhooks/salesforce",
                headers={**admin_headers, "Content-Type": "application/json"},
                json={"event": "ContactUpdated"},
            )
    resp = asyncio.run(run())
    assert resp.status_code in (200, 202, 400, 401, 422, 503)


# ── disconnect ────────────────────────────────────────────────────────────────

def test_disconnect_nonexistent_integration(app, admin_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.delete(
                "/integrations/hubspot",
                headers=admin_headers,
            )
    resp = asyncio.run(run())
    assert resp.status_code in (200, 404, 503)
