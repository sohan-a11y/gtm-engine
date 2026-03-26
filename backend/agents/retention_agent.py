from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.agents.base_agent import AgentRunContext, BaseAgent, load_prompt_template


@dataclass(slots=True)
class RetentionResult:
    health_score: float
    health_state: str
    churn_driver: str
    playbook: str
    renewal_probability: float
    state_transition: str | None = None
    alert_required: bool = False
    signals: list[str] = field(default_factory=list)


class RetentionAgent(BaseAgent):
    agent_name = "retention_agent"

    async def analyze(
        self,
        *,
        account: dict[str, Any],
        previous_health_score: float | None = None,
    ) -> RetentionResult:
        prompt = load_prompt_template("retention_analysis", "Analyze account health and churn risk.")
        payload = await self.call_llm_json(
            system_prompt=prompt,
            user_prompt=self._build_prompt(account=account, previous_health_score=previous_health_score),
            fallback=lambda: self._fallback(account, previous_health_score),
        )
        score = max(0.0, min(1.0, float(payload.get("health_score", 0.0))))
        state = str(payload.get("health_state", self._health_state(score)))
        return RetentionResult(
            health_score=score,
            health_state=state,
            churn_driver=str(payload.get("churn_driver", self._churn_driver(account))),
            playbook=str(payload.get("playbook", self._playbook_for_state(state))),
            renewal_probability=max(0.0, min(1.0, float(payload.get("renewal_probability", 0.5)))),
            state_transition=self._state_transition(previous_health_score, score),
            alert_required=score < 0.4 or self._state_is_degrading(previous_health_score, score),
            signals=list(payload.get("signals", [])),
        )

    async def run(self, payload: dict[str, Any], context: AgentRunContext | None = None) -> Any:
        return await self.analyze(
            account=dict(payload.get("account", {})),
            previous_health_score=payload.get("previous_health_score"),
        )

    def _build_prompt(self, *, account: dict[str, Any], previous_health_score: float | None) -> str:
        return f"ACCOUNT: {account}\nPREVIOUS_SCORE: {previous_health_score!r}"

    def _fallback(self, account: dict[str, Any], previous_health_score: float | None) -> dict[str, Any]:
        score = 0.72
        if float(account.get("dau_mau", 0.0) or 0.0) < 0.3:
            score -= 0.15
        if int(account.get("open_tickets", 0) or 0) > 5:
            score -= 0.1
        if previous_health_score is not None and previous_health_score - score > 0.15:
            score -= 0.05
        score = max(0.0, min(1.0, score))
        state = self._health_state(score)
        return {
            "health_score": score,
            "health_state": state,
            "churn_driver": self._churn_driver(account),
            "playbook": self._playbook_for_state(state),
            "renewal_probability": max(0.0, min(1.0, score + 0.1)),
            "state_transition": self._state_transition(previous_health_score, score),
            "alert_required": score < 0.4,
            "signals": ["usage_down", "tickets_up"] if score < 0.5 else ["healthy_usage"],
        }

    def _health_state(self, score: float) -> str:
        if score >= 0.8:
            return "Thriving"
        if score >= 0.6:
            return "Stable"
        if score >= 0.4:
            return "At Risk"
        if score >= 0.2:
            return "In Danger"
        return "Critical"

    def _playbook_for_state(self, state: str) -> str:
        mapping = {
            "Thriving": "expand_and_upsell",
            "Stable": "maintain_success_plan",
            "At Risk": "focused_success_review",
            "In Danger": "escalated_intervention",
            "Critical": "executive_save_plan",
        }
        return mapping.get(state, "maintain_success_plan")

    def _churn_driver(self, account: dict[str, Any]) -> str:
        if int(account.get("open_tickets", 0) or 0) > 5:
            return "support_issues"
        if float(account.get("feature_adoption", 0.0) or 0.0) < 0.3:
            return "low_usage"
        if account.get("champion_left"):
            return "champion_left"
        return "budget_concerns"

    def _state_transition(self, previous_score: float | None, score: float) -> str | None:
        if previous_score is None:
            return None
        previous_state = self._health_state(previous_score)
        current_state = self._health_state(score)
        if previous_state == current_state:
            return None
        return f"{previous_state.lower()}_to_{current_state.lower().replace(' ', '_')}"

    def _state_is_degrading(self, previous_score: float | None, score: float) -> bool:
        return previous_score is not None and score < previous_score
