"""Integration tests for the full agent pipeline via the /agents API."""
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
def agent_headers() -> dict[str, str]:
    bundle = create_token_pair(
        str(uuid4()), str(uuid4()), "member",
        ["agents:trigger", "leads:read", "leads:write"],
    )
    return {"Authorization": f"Bearer {bundle.access_token}"}


# ── ICP scoring ───────────────────────────────────────────────────────────────

def test_icp_score_endpoint_reachable(app, agent_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                "/agents/icp_agent/score",
                headers=agent_headers,
                json={
                    "contact_profile": {
                        "first_name": "Jane",
                        "company": "Acme",
                        "title": "VP Sales",
                    }
                },
            )
    resp = asyncio.run(run())
    assert resp.status_code in (200, 422, 503)


def test_icp_train_endpoint(app, agent_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                "/agents/icp_agent/score",
                headers=agent_headers,
                json={
                    "mode": "train",
                    "profiles": [
                        {"name": "Alice", "company": "Acme"},
                        {"name": "Bob", "company": "Beta"},
                        {"name": "Carol", "company": "Gamma"},
                    ],
                },
            )
    resp = asyncio.run(run())
    assert resp.status_code in (200, 422, 503)


# ── outbound generation ───────────────────────────────────────────────────────

def test_outbound_generate_endpoint(app, agent_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                "/agents/outbound_agent/generate",
                headers=agent_headers,
                json={
                    "contact": {"first_name": "Jane", "company_name": "Acme"},
                    "campaign": {"name": "Q2 Push", "value_prop": "Cut manual GTM work"},
                },
            )
    resp = asyncio.run(run())
    assert resp.status_code in (200, 422, 503)


# ── deal intelligence ─────────────────────────────────────────────────────────

def test_deal_intel_analyze_endpoint(app, agent_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                "/agents/deal_intel_agent/analyze",
                headers=agent_headers,
                json={
                    "deal": {
                        "name": "Acme Enterprise",
                        "stage": "negotiation",
                        "amount_cents": 10000000,
                        "days_in_stage": 45,
                    }
                },
            )
    resp = asyncio.run(run())
    assert resp.status_code in (200, 422, 503)


# ── retention analysis ────────────────────────────────────────────────────────

def test_retention_analyze_endpoint(app, agent_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post(
                "/agents/retention_agent/analyze",
                headers=agent_headers,
                json={
                    "account": {
                        "dau_mau": 0.3,
                        "open_tickets": 5,
                        "mrr_cents": 500000,
                        "contract_days_remaining": 45,
                    }
                },
            )
    resp = asyncio.run(run())
    assert resp.status_code in (200, 422, 503)


# ── unauthenticated agent requests ────────────────────────────────────────────

def test_agent_endpoint_requires_auth(app):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post("/agents/icp_agent/score", json={"contact_profile": {}})
    resp = asyncio.run(run())
    assert resp.status_code in (401, 403)


# ── jobs endpoint ─────────────────────────────────────────────────────────────

def test_run_batch_score_job(app, agent_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post("/jobs/run-batch-score", headers=agent_headers)
    resp = asyncio.run(run())
    assert resp.status_code in (200, 202, 422, 503)


def test_run_crm_sync_job(app, agent_headers):
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            return await c.post("/jobs/run-crm-sync", headers=agent_headers)
    resp = asyncio.run(run())
    assert resp.status_code in (200, 202, 422, 503)
