from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from backend.agents.base_agent import AgentRunContext, BaseAgent, load_prompt_template


@dataclass(slots=True)
class OutboundVariation:
    subject: str
    body: str
    hook_type: str
    confidence: float


@dataclass(slots=True)
class OutboundResult:
    variations: list[OutboundVariation]
    validation_flags: list[str] = field(default_factory=list)
    campaign_name: str | None = None


class OutboundAgent(BaseAgent):
    agent_name = "outbound_agent"

    async def generate_variations(
        self,
        *,
        contact: dict[str, Any],
        campaign: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> OutboundResult:
        prompt = load_prompt_template("outbound_personalization", "Generate three outbound email variations.")
        user_prompt = self._build_prompt(contact=contact, campaign=campaign, context=context)
        payload = await self.call_llm_json(system_prompt=prompt, user_prompt=user_prompt, fallback=lambda: self._fallback(contact, campaign))
        variations = [self._normalize_variation(item) for item in payload.get("variations", [])]
        if len(variations) < 3:
            fallback_variations = [self._normalize_variation(item) for item in self._fallback(contact, campaign)["variations"]]
            for variation in fallback_variations:
                if len(variations) >= 3:
                    break
                variations.append(variation)
        flags = self._collect_validation_flags(variations)
        return OutboundResult(variations=variations, validation_flags=flags, campaign_name=campaign.get("name"))

    async def run(self, payload: dict[str, Any], context: AgentRunContext | None = None) -> Any:
        return await self.generate_variations(
            contact=dict(payload.get("contact", {})),
            campaign=dict(payload.get("campaign", {})),
            context=dict(payload.get("context", {})) or None,
        )

    def _build_prompt(
        self,
        *,
        contact: dict[str, Any],
        campaign: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> str:
        return (
            f"CONTACT:\n{contact}\n\n"
            f"CAMPAIGN:\n{campaign}\n\n"
            f"CONTEXT:\n{context or {}}"
        )

    def _fallback(self, contact: dict[str, Any], campaign: dict[str, Any]) -> dict[str, Any]:
        first_name = contact.get("first_name", "there")
        company = contact.get("company_name", "your team")
        body = (
            f"Hi {first_name}, I noticed a few signals that suggest we could help {company} move faster. "
            "Would you be open to a brief conversation next week?"
        )
        return {
            "variations": [
                {
                    "subject": f"Quick idea for {company}",
                    "body": body,
                    "hook_type": "pain_point",
                    "confidence": 0.73,
                },
                {
                    "subject": f"Thoughts for {company}",
                    "body": (
                        f"Hi {first_name}, based on what I saw about {company}, I think there may be a fit around "
                        f"{campaign.get('value_prop', 'reducing manual GTM work')}. Open to a short chat?"
                    ),
                    "hook_type": "recent_news",
                    "confidence": 0.69,
                },
                {
                    "subject": f"Reaching out to {company}",
                    "body": (
                        f"Hi {first_name}, I was reviewing companies like {company} and saw a strong opportunity "
                        "to improve outbound consistency. Could we compare notes?"
                    ),
                    "hook_type": "job_posting",
                    "confidence": 0.66,
                },
            ]
        }

    def _normalize_variation(self, item: Any) -> OutboundVariation:
        body = str(item.get("body", "")).strip()
        if len(body.split()) > 150:
            body = " ".join(body.split()[:150])
        if "?" not in body:
            body = f"{body} Would you be open to a quick chat?"
        return OutboundVariation(
            subject=str(item.get("subject", "")).strip(),
            body=body,
            hook_type=str(item.get("hook_type", "pain_point")),
            confidence=max(0.0, min(1.0, float(item.get("confidence", 0.5)))),
        )

    def _collect_validation_flags(self, variations: list[OutboundVariation]) -> list[str]:
        flags: list[str] = []
        for variation in variations:
            if len(variation.body.split()) > 150 and "over_length" not in flags:
                flags.append("over_length")
            if re.search(r"\bai\b", variation.body.lower()) and "mentions_ai" not in flags:
                flags.append("mentions_ai")
            if "?" not in variation.body and "missing_cta" not in flags:
                flags.append("missing_cta")
        return flags
