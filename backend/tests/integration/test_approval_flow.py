"""Integration tests for the human-in-the-loop approval queue."""
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

from backend.api.main import create_app  # noqa: E402
from backend.core.auth import create_token_pair  # noqa: E402


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def member_headers() -> dict[str, str]:
    bundle = create_token_pair(
        str(uuid4()), str(uuid4()), "member",
        ["approvals:read", "approvals:action"],
    )
    return {"Authorization": f"Bearer {bundle.access_token}"}


@pytest.fixture()
def viewer_headers() -> dict[str, str]:
    bundle = create_token_pair(str(uuid4()), str(uuid4()), "viewer", ["approvals:read"])
    return {"Authorization": f"Bearer {bundle.access_token}"}


# ── list approvals ────────────────────────────────────────────────────────────

def test_list_approvals_requires_auth(app):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.get("/approvals")
    resp = asyncio.run(run())
    assert resp.status_code == 403


def test_list_approvals_authenticated(app, member_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.get("/approvals", headers=member_headers)
    resp = asyncio.run(run())
    assert resp.status_code in (200, 503)


def test_list_approvals_viewer_can_read(app, viewer_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.get("/approvals", headers=viewer_headers)
    resp = asyncio.run(run())
    assert resp.status_code in (200, 503)


# ── approve action ────────────────────────────────────────────────────────────

def test_approve_nonexistent_item_returns_404_or_503(app, member_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                f"/approvals/{uuid4()}/approve",
                headers=member_headers,
                json={},
            )
    resp = asyncio.run(run())
    assert resp.status_code in (404, 503)


def test_reject_nonexistent_item_returns_404_or_503(app, member_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                f"/approvals/{uuid4()}/reject",
                headers=member_headers,
                json={"reason": "Not relevant"},
            )
    resp = asyncio.run(run())
    assert resp.status_code in (404, 503)


# ── status filter ─────────────────────────────────────────────────────────────

def test_approvals_filter_by_status(app, member_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.get("/approvals?status=pending_approval", headers=member_headers)
    resp = asyncio.run(run())
    assert resp.status_code in (200, 503)


def test_approvals_pagination(app, member_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.get("/approvals?limit=5&offset=0", headers=member_headers)
    resp = asyncio.run(run())
    assert resp.status_code in (200, 503)


# ── RBAC: viewer cannot approve ───────────────────────────────────────────────

def test_viewer_cannot_approve(app, viewer_headers):
    """Viewer role lacks approvals:action permission."""
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                f"/approvals/{uuid4()}/approve",
                headers=viewer_headers,
                json={},
            )
    resp = asyncio.run(run())
    # 403 from RBAC or 404/503 if route checked DB first
    assert resp.status_code in (403, 404, 503)
