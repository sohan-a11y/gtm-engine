from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.agents.base_agent import AgentRunContext, BaseAgent, load_prompt_template


@dataclass(slots=True)
class DealIntelResult:
    risk_score: float
    risk_level: str
    risk_factors: list[dict[str, Any]] = field(default_factory=list)
    positive_signals: list[str] = field(default_factory=list)
    recommended_actions: list[dict[str, Any]] = field(default_factory=list)
    likely_close_date: datetime | None = None
    deal_summary: str = ""


class DealIntelAgent(BaseAgent):
    agent_name = "deal_intel_agent"

    async def analyze(
        self,
        *,
        deal: dict[str, Any],
        transcript_summary: str | None = None,
        engagement_metrics: dict[str, Any] | None = None,
        competitor_mentions: list[str] | None = None,
    ) -> DealIntelResult:
        prompt = load_prompt_template("deal_intelligence", "Analyze deal risk and recommend actions.")
        payload = await self.call_llm_json(
            system_prompt=prompt,
            user_prompt=self._build_prompt(
                deal=deal,
                transcript_summary=transcript_summary,
                engagement_metrics=engagement_metrics,
                competitor_mentions=competitor_mentions,
            ),
            fallback=lambda: self._fallback(deal, transcript_summary, engagement_metrics, competitor_mentions),
        )
        score = max(0.0, min(1.0, float(payload.get("risk_score", 0.0))))
        return DealIntelResult(
            risk_score=score,
            risk_level=str(payload.get("risk_level", self._risk_level(score))),
            risk_factors=list(payload.get("risk_factors", [])),
            positive_signals=list(payload.get("positive_signals", [])),
            recommended_actions=list(payload.get("recommended_actions", [])),
            likely_close_date=self._parse_close_date(payload.get("likely_close_date"), deal),
            deal_summary=str(payload.get("deal_summary", "")),
        )

    async def run(self, payload: dict[str, Any], context: AgentRunContext | None = None) -> Any:
        return await self.analyze(
            deal=dict(payload.get("deal", {})),
            transcript_summary=payload.get("transcript_summary"),
            engagement_metrics=dict(payload.get("engagement_metrics", {})) or None,
            competitor_mentions=list(payload.get("competitor_mentions", [])) or None,
        )

    def _build_prompt(
        self,
        *,
        deal: dict[str, Any],
        transcript_summary: str | None,
        engagement_metrics: dict[str, Any] | None,
        competitor_mentions: list[str] | None,
    ) -> str:
        return (
            f"DEAL: {deal}\n"
            f"TRANSCRIPT_SUMMARY: {transcript_summary or ''}\n"
            f"ENGAGEMENT: {engagement_metrics or {}}\n"
            f"COMPETITORS: {competitor_mentions or []}"
        )

    def _fallback(
        self,
        deal: dict[str, Any],
        transcript_summary: str | None,
        engagement_metrics: dict[str, Any] | None,
        competitor_mentions: list[str] | None,
    ) -> dict[str, Any]:
        score = 0.35
        days_in_stage = int(deal.get("days_in_stage", 0) or 0)
        if days_in_stage > 30:
            score += 0.2
        if float(deal.get("amount_cents", 0) or 0) > 1_000_000:
            score += 0.1
        if engagement_metrics and float(engagement_metrics.get("reply_rate", 0)) > 0.2:
            score -= 0.1
        score = max(0.0, min(1.0, score))
        return {
            "risk_score": score,
            "risk_level": self._risk_level(score),
            "risk_factors": [{"factor": "stage_stall", "severity": "medium"}] if days_in_stage > 20 else [],
            "positive_signals": ["active-engagement"] if engagement_metrics else [],
            "recommended_actions": [
                {"action": "schedule_follow_up", "owner": "AE", "urgency": "this_week"}
            ],
            "likely_close_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "deal_summary": "The deal shows moderate risk and should be monitored closely. A proactive follow-up is recommended.",
        }

    def _risk_level(self, score: float) -> str:
        if score >= 0.8:
            return "critical"
        if score >= 0.6:
            return "high"
        if score >= 0.4:
            return "medium"
        return "low"

    def _parse_close_date(self, value: Any, deal: dict[str, Any]) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return deal.get("close_date")
