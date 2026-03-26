"""Unit tests for backend/core/context_builder.py"""
from __future__ import annotations

import pytest

from backend.core.context_builder import ContextBuilder, _format_section, build_context_builder


@pytest.fixture()
def cb() -> ContextBuilder:
    return ContextBuilder()


# ── _format_section ───────────────────────────────────────────────────────────

def test_format_section_with_data():
    result = _format_section("contact", {"name": "Jane", "title": "VP"})
    assert "contact:" in result
    assert "Jane" in result
    assert "VP" in result


def test_format_section_none_returns_none_string():
    result = _format_section("company", None)
    assert result == "company: none"


def test_format_section_empty_dict_returns_none_string():
    result = _format_section("enrichment", {})
    assert result == "enrichment: none"


# ── build_profile_text ────────────────────────────────────────────────────────

def test_build_profile_text_includes_all_keys(cb):
    profile = {"name": "Alice", "company": "Acme", "title": "CTO"}
    text = cb.build_profile_text(profile)
    assert "name: Alice" in text
    assert "company: Acme" in text
    assert "title: CTO" in text


def test_build_profile_text_empty_profile(cb):
    text = cb.build_profile_text({})
    assert text == ""


# ── build_lead_context ────────────────────────────────────────────────────────

def test_build_lead_context_with_all_sections(cb):
    ctx = cb.build_lead_context(
        contact={"email": "jane@acme.com"},
        company={"name": "Acme"},
        enrichment={"source": "apollo"},
    )
    assert "contact:" in ctx
    assert "company:" in ctx
    assert "enrichment:" in ctx


def test_build_lead_context_missing_company_shows_none(cb):
    ctx = cb.build_lead_context(contact={"email": "jane@acme.com"})
    assert "company: none" in ctx


def test_build_lead_context_missing_enrichment_shows_none(cb):
    ctx = cb.build_lead_context(contact={"email": "j@a.com"}, company={"name": "Acme"})
    assert "enrichment: none" in ctx


# ── build_campaign_context ────────────────────────────────────────────────────

def test_build_campaign_context(cb):
    ctx = cb.build_campaign_context(
        campaign={"name": "Q2", "value_prop": "Save time"},
        contact={"first_name": "Bob"},
    )
    assert "campaign:" in ctx
    assert "contact:" in ctx
    assert "Q2" in ctx
    assert "Bob" in ctx


# ── build_full_outbound_context ───────────────────────────────────────────────

def test_build_full_outbound_context_all_sections(cb):
    ctx = cb.build_full_outbound_context(
        contact={"email": "bob@co.com"},
        campaign={"name": "Outbound Q3"},
        enrichment={"technologies": ["Salesforce"]},
        extra_signals={"intent": "high"},
    )
    assert "contact:" in ctx
    assert "campaign:" in ctx
    assert "signals:" in ctx
    assert "Outbound Q3" in ctx
    assert "Salesforce" in ctx


def test_build_full_outbound_context_minimal(cb):
    ctx = cb.build_full_outbound_context(
        contact={"email": "x@y.com"},
        campaign={"name": "Basic"},
    )
    assert "campaign:" in ctx
    assert "signals: none" in ctx


# ── factory function ──────────────────────────────────────────────────────────

def test_build_context_builder_returns_instance():
    assert isinstance(build_context_builder(), ContextBuilder)
