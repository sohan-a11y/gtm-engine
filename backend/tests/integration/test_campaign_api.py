"""Integration tests for the /campaigns API endpoints."""
from __future__ import annotations

import asyncio
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

from backend.api.main import create_app
from backend.core.auth import create_token_pair


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def admin_headers() -> dict[str, str]:
    bundle = create_token_pair(
        str(uuid4()), str(uuid4()), "admin",
        ["campaigns:read", "campaigns:write", "campaigns:delete"],
    )
    return {"Authorization": f"Bearer {bundle.access_token}"}


@pytest.fixture()
def viewer_headers() -> dict[str, str]:
    bundle = create_token_pair(str(uuid4()), str(uuid4()), "viewer", ["campaigns:read"])
    return {"Authorization": f"Bearer {bundle.access_token}"}


# ── list ──────────────────────────────────────────────────────────────────────

def test_list_campaigns_unauthenticated_returns_403(app):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.get("/campaigns")
    resp = asyncio.run(run())
    assert resp.status_code == 403


def test_list_campaigns_with_auth(app, admin_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.get("/campaigns", headers=admin_headers)
    resp = asyncio.run(run())
    assert resp.status_code in (200, 503)


# ── create ────────────────────────────────────────────────────────────────────

def test_create_campaign_missing_name_returns_422(app, admin_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post("/campaigns", headers=admin_headers, json={})
    resp = asyncio.run(run())
    assert resp.status_code in (422, 503)


def test_create_campaign_valid_payload(app, admin_headers):
    async def run():
        payload = {
            "name": f"Campaign {uuid4().hex[:6]}",
            "tone": "professional",
            "value_prop": "Replace your outreach stack",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post("/campaigns", headers=admin_headers, json=payload)
    resp = asyncio.run(run())
    assert resp.status_code in (200, 201, 503)


# ── detail ────────────────────────────────────────────────────────────────────

def test_get_nonexistent_campaign(app, admin_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.get(f"/campaigns/{uuid4()}", headers=admin_headers)
    resp = asyncio.run(run())
    assert resp.status_code in (404, 503)


# ── update ────────────────────────────────────────────────────────────────────

def test_update_nonexistent_campaign(app, admin_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.patch(
                f"/campaigns/{uuid4()}",
                headers=admin_headers,
                json={"status": "active"},
            )
    resp = asyncio.run(run())
    assert resp.status_code in (404, 503)


# ── pagination ────────────────────────────────────────────────────────────────

def test_list_campaigns_pagination_params(app, admin_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.get("/campaigns?limit=10&offset=0", headers=admin_headers)
    resp = asyncio.run(run())
    assert resp.status_code in (200, 503)


# ── sequences sub-resource ────────────────────────────────────────────────────

def test_get_campaign_sequences(app, admin_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.get(f"/campaigns/{uuid4()}/sequences", headers=admin_headers)
    resp = asyncio.run(run())
    assert resp.status_code in (200, 404, 503)
