"""Unit tests for backend/agents/outbound_agent.py"""
from __future__ import annotations

import asyncio

import pytest

from backend.agents.base_agent import LocalLLMRouter
from backend.agents.outbound_agent import OutboundAgent, OutboundResult, OutboundVariation


@pytest.fixture()
def agent() -> OutboundAgent:
    return OutboundAgent(llm_router=LocalLLMRouter())


@pytest.fixture()
def contact() -> dict:
    return {"first_name": "Jane", "last_name": "Doe", "company_name": "Acme Corp", "title": "VP Revenue"}


@pytest.fixture()
def campaign() -> dict:
    return {"name": "Q3 Outbound", "value_prop": "reduce manual GTM work", "tone": "professional"}


# ── generate_variations ───────────────────────────────────────────────────────

def test_generates_exactly_three_variations(agent, contact, campaign):
    async def run():
        return await agent.generate_variations(contact=contact, campaign=campaign)
    result = asyncio.run(run())
    assert isinstance(result, OutboundResult)
    assert len(result.variations) == 3


def test_variations_have_required_fields(agent, contact, campaign):
    async def run():
        return await agent.generate_variations(contact=contact, campaign=campaign)
    result = asyncio.run(run())
    for v in result.variations:
        assert isinstance(v, OutboundVariation)
        assert v.subject
        assert v.body
        assert v.hook_type
        assert 0.0 <= v.confidence <= 1.0


def test_variations_include_campaign_name(agent, contact, campaign):
    async def run():
        return await agent.generate_variations(contact=contact, campaign=campaign)
    result = asyncio.run(run())
    assert result.campaign_name == "Q3 Outbound"


def test_bodies_contain_cta_question_mark(agent, contact, campaign):
    async def run():
        return await agent.generate_variations(contact=contact, campaign=campaign)
    result = asyncio.run(run())
    for v in result.variations:
        assert "?" in v.body, f"No CTA found in: {v.body}"


def test_bodies_under_150_words(agent, contact, campaign):
    async def run():
        return await agent.generate_variations(contact=contact, campaign=campaign)
    result = asyncio.run(run())
    for v in result.variations:
        assert len(v.body.split()) <= 150


def test_validation_flags_is_list(agent, contact, campaign):
    async def run():
        return await agent.generate_variations(contact=contact, campaign=campaign)
    result = asyncio.run(run())
    assert isinstance(result.validation_flags, list)


def test_generates_with_optional_context(agent, contact, campaign):
    async def run():
        return await agent.generate_variations(
            contact=contact,
            campaign=campaign,
            context={"recent_news": "Acme raised $50M Series B"},
        )
    result = asyncio.run(run())
    assert len(result.variations) == 3


# ── run dispatch ──────────────────────────────────────────────────────────────

def test_run_dispatches_to_generate_variations(agent, contact, campaign):
    async def run():
        return await agent.run({"contact": contact, "campaign": campaign})
    result = asyncio.run(run())
    assert isinstance(result, OutboundResult)
    assert len(result.variations) == 3


# ── normalize_variation ────────────────────────────────────────────────────────

def test_normalize_truncates_over_150_words(agent):
    long_body = " ".join(["word"] * 200)
    variation = agent._normalize_variation({"subject": "Hi", "body": long_body, "hook_type": "pain_point", "confidence": 0.8})
    assert len(variation.body.split()) <= 150


def test_normalize_adds_cta_if_missing(agent):
    variation = agent._normalize_variation({
        "subject": "Hi",
        "body": "This is a body without a question mark",
        "hook_type": "pain_point",
        "confidence": 0.8,
    })
    assert "?" in variation.body


def test_normalize_clamps_confidence(agent):
    v_high = agent._normalize_variation({"subject": "s", "body": "b?", "hook_type": "t", "confidence": 99.9})
    v_low = agent._normalize_variation({"subject": "s", "body": "b?", "hook_type": "t", "confidence": -5.0})
    assert v_high.confidence == 1.0
    assert v_low.confidence == 0.0


# ── validation flags ──────────────────────────────────────────────────────────

def test_flags_mentions_ai_when_ai_in_body(agent):
    variations = [
        OutboundVariation(subject="s", body="This AI-powered solution?", hook_type="t", confidence=0.5),
    ]
    flags = agent._collect_validation_flags(variations)
    assert "mentions_ai" in flags


def test_no_false_flags_on_clean_email(agent):
    variations = [
        OutboundVariation(subject="Quick idea for Acme", body="Hi Jane, would you be open to a call?", hook_type="pain_point", confidence=0.8),
    ]
    flags = agent._collect_validation_flags(variations)
    assert "mentions_ai" not in flags
    assert "over_length" not in flags
    assert "missing_cta" not in flags
