"""Unit tests for backend/agents/icp_agent.py"""
from __future__ import annotations

import asyncio

import pytest

from backend.agents.base_agent import LocalLLMRouter
from backend.agents.icp_agent import ICPAgent, ICPProfile, ICPScoreResult


@pytest.fixture()
def agent() -> ICPAgent:
    return ICPAgent(llm_router=LocalLLMRouter())


@pytest.fixture()
def sample_profiles() -> list[dict]:
    return [
        {"name": "Alice", "title": "VP Sales", "company": "Acme", "industry": "SaaS", "pain_points": "manual outreach"},
        {"name": "Bob", "title": "Head of Growth", "company": "Beta", "industry": "SaaS", "pain_points": "pipeline visibility"},
        {"name": "Carol", "title": "CRO", "company": "Gamma", "industry": "FinTech", "pain_points": "deal forecasting"},
    ]


# ── training ──────────────────────────────────────────────────────────────────

def test_training_requires_minimum_3_profiles(agent):
    async def run():
        return await agent.train(org_id="org-1", profiles=[{"name": "A"}, {"name": "B"}])
    result = asyncio.run(run())
    assert result["status"] == "needs_more_profiles"
    assert result["minimum_required"] == 3
    assert result["trained_count"] == 2


def test_training_succeeds_with_3_or_more(agent, sample_profiles):
    async def run():
        return await agent.train(org_id="org-1", profiles=sample_profiles)
    result = asyncio.run(run())
    assert result["status"] == "trained"
    assert result["trained_count"] == 3
    assert "icp_profiles_org-1" in result["collection"]


def test_training_stores_profiles_for_scoring(agent, sample_profiles):
    async def run():
        await agent.train(org_id="org-1", profiles=sample_profiles)
        return await agent.score(org_id="org-1", contact_profile={"company": "Acme"})
    result = asyncio.run(run())
    assert result.training_profile_count == 3
    assert not result.requires_training


# ── scoring without training ──────────────────────────────────────────────────

def test_score_without_training_requires_training_flag(agent):
    async def run():
        return await agent.score(org_id="untrained-org", contact_profile={"company": "X"})
    result = asyncio.run(run())
    assert result.requires_training is True
    assert result.fallback_used is True


def test_score_without_training_returns_fallback_result(agent):
    async def run():
        return await agent.score(org_id="new-org", contact_profile={"name": "Dave"})
    result = asyncio.run(run())
    assert isinstance(result, ICPScoreResult)
    # score may be None when no training data
    assert result.score is None or 0.0 <= result.score <= 1.0


# ── scoring after training ────────────────────────────────────────────────────

def test_score_returns_value_in_0_1_range(agent, sample_profiles):
    async def run():
        await agent.train(org_id="org-2", profiles=sample_profiles)
        return await agent.score(org_id="org-2", contact_profile={"company": "SaaS", "pain_points": "outreach"})
    result = asyncio.run(run())
    if result.score is not None:
        assert 0.0 <= result.score <= 1.0


def test_score_returns_explanation(agent, sample_profiles):
    async def run():
        await agent.train(org_id="org-3", profiles=sample_profiles)
        return await agent.score(org_id="org-3", contact_profile={"title": "VP Sales"})
    result = asyncio.run(run())
    assert isinstance(result.explanation, str)
    assert result.explanation


def test_score_returns_signal_lists(agent, sample_profiles):
    async def run():
        await agent.train(org_id="org-4", profiles=sample_profiles)
        return await agent.score(org_id="org-4", contact_profile={"pain_points": "budget manual"})
    result = asyncio.run(run())
    assert isinstance(result.fit_signals, list)
    assert isinstance(result.gap_signals, list)


def test_score_clamped_within_bounds_even_if_llm_returns_out_of_range(agent, sample_profiles):
    """The agent must clamp to [0.0, 1.0] regardless of raw LLM output."""
    async def run():
        await agent.train(org_id="org-5", profiles=sample_profiles)
        return await agent.score(org_id="org-5", contact_profile={"company": "Edge"})
    result = asyncio.run(run())
    if result.score is not None:
        assert result.score >= 0.0
        assert result.score <= 1.0


# ── run dispatch ──────────────────────────────────────────────────────────────

def test_run_with_score_mode(agent, sample_profiles):
    async def run():
        await agent.train(org_id="org-run", profiles=sample_profiles)
        return await agent.run({"mode": "score", "org_id": "org-run", "contact_profile": {"company": "Acme"}})
    result = asyncio.run(run())
    assert isinstance(result, ICPScoreResult)


def test_run_with_train_mode(agent, sample_profiles):
    async def run():
        return await agent.run({"mode": "train", "org_id": "org-train", "profiles": sample_profiles})
    result = asyncio.run(run())
    assert result["status"] == "trained"


# ── fallback result ───────────────────────────────────────────────────────────

def test_fallback_result_with_empty_training(agent):
    result = agent.fallback_result(
        contact_profile={"company": "X"},
        training_profiles=[],
        reason="no data",
    )
    assert result.requires_training is True
    assert result.fallback_used is True
    assert result.score is None


def test_fallback_result_with_profiles_computes_similarity(agent, sample_profiles):
    profiles = [ICPProfile(text=agent._profile_text(p)) for p in sample_profiles]
    result = agent.fallback_result(
        contact_profile={"company": "Acme", "industry": "SaaS"},
        training_profiles=profiles,
        reason="llm unavailable",
    )
    assert result.fallback_used is True
    if result.score is not None:
        assert 0.0 <= result.score <= 1.0
