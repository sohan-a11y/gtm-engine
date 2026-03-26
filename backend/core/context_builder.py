from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping


def _format_section(title: str, payload: Mapping[str, Any] | None) -> str:
    if not payload:
        return f"{title}: none"
    return f"{title}: {json.dumps(payload, indent=2, sort_keys=True, default=str)}"


@dataclass(slots=True)
class ContextBuilder:
    def build_profile_text(self, profile: Mapping[str, Any]) -> str:
        lines = []
        for key, value in profile.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def build_lead_context(
        self,
        contact: Mapping[str, Any],
        company: Mapping[str, Any] | None = None,
        enrichment: Mapping[str, Any] | None = None,
    ) -> str:
        parts = [
            _format_section("contact", contact),
            _format_section("company", company),
            _format_section("enrichment", enrichment),
        ]
        return "\n\n".join(parts)

    def build_campaign_context(self, campaign: Mapping[str, Any], contact: Mapping[str, Any]) -> str:
        return "\n\n".join(
            [
                _format_section("campaign", campaign),
                _format_section("contact", contact),
            ]
        )

    def build_full_outbound_context(
        self,
        contact: Mapping[str, Any],
        campaign: Mapping[str, Any],
        enrichment: Mapping[str, Any] | None = None,
        extra_signals: Mapping[str, Any] | None = None,
    ) -> str:
        return "\n\n".join(
            [
                self.build_lead_context(contact, enrichment=enrichment),
                _format_section("campaign", campaign),
                _format_section("signals", extra_signals),
            ]
        )


def build_context_builder() -> ContextBuilder:
    return ContextBuilder()
