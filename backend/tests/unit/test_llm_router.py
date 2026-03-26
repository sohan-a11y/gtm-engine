"""Unit tests for backend/core/llm_router.py"""
from __future__ import annotations

import asyncio
import json

import pytest

from backend.core.llm_router import LLMResponse, LLMRouter, build_llm_router


@pytest.fixture()
def router() -> LLMRouter:
    """Mock router (no real LLM credentials)."""
    return LLMRouter(provider="mock", model="mock-model", api_key=None)


# ── complete ──────────────────────────────────────────────────────────────────

def test_complete_returns_llm_response(router):
    async def run():
        return await router.complete(system="You are a helper.", user="Say hi.")
    resp = asyncio.run(run())
    assert isinstance(resp, LLMResponse)
    assert isinstance(resp.content, str)
    assert resp.content


def test_complete_json_format_returns_valid_json(router):
    async def run():
        return await router.complete(system="Score leads.", user="Contact: Alice.", format="json")
    resp = asyncio.run(run())
    parsed = json.loads(resp.content)
    assert "score" in parsed
    assert "variations" in parsed


def test_complete_text_format_returns_string(router):
    async def run():
        return await router.complete(system="Help.", user="What is GTM?", format="text")
    resp = asyncio.run(run())
    assert isinstance(resp.content, str)
    assert not resp.content.startswith("{")


def test_complete_is_deterministic_for_same_input(router):
    async def run():
        r1 = await router.complete(system="sys", user="usr", format="json")
        r2 = await router.complete(system="sys", user="usr", format="json")
        return r1.content, r2.content
    c1, c2 = asyncio.run(run())
    assert c1 == c2


def test_complete_differs_for_different_input(router):
    async def run():
        r1 = await router.complete(system="sys", user="user A", format="json")
        r2 = await router.complete(system="sys", user="user B", format="json")
        return r1.content, r2.content
    c1, c2 = asyncio.run(run())
    assert c1 != c2


def test_complete_provider_fields(router):
    async def run():
        return await router.complete(system="s", user="u")
    resp = asyncio.run(run())
    assert resp.provider == "mock"
    assert resp.model == "mock-model"
    assert resp.prompt_tokens == 0
    assert resp.completion_tokens == 0
    assert resp.cost_usd == 0.0


def test_complete_with_metadata_does_not_raise(router):
    async def run():
        return await router.complete(
            system="s", user="u",
            metadata={"org_id": "org-1", "agent_name": "icp_agent"},
        )
    resp = asyncio.run(run())
    assert resp.content


# ── embed ─────────────────────────────────────────────────────────────────────

def test_embed_returns_1536_floats(router):
    async def run():
        return await router.embed("Contact: Jane VP Revenue Acme")
    emb = asyncio.run(run())
    assert len(emb) == 1536
    assert all(0.0 <= v <= 1.0 for v in emb)


def test_embed_is_deterministic(router):
    async def run():
        e1 = await router.embed("text")
        e2 = await router.embed("text")
        return e1, e2
    e1, e2 = asyncio.run(run())
    assert e1 == e2


def test_embed_differs_for_different_text(router):
    async def run():
        return await router.embed("text A"), await router.embed("text B")
    e1, e2 = asyncio.run(run())
    assert e1 != e2


# ── build helper ──────────────────────────────────────────────────────────────

def test_build_llm_router_returns_instance():
    r = build_llm_router()
    assert isinstance(r, LLMRouter)
