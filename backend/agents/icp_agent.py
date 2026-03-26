from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Any

from backend.agents.base_agent import AgentRunContext, BaseAgent, load_prompt_template, _word_overlap


@dataclass(slots=True)
class ICPProfile:
    text: str
    label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ICPScoreResult:
    score: float | None
    explanation: str
    fit_signals: list[str]
    gap_signals: list[str]
    requires_training: bool = False
    fallback_used: bool = False
    similarity_score: float | None = None
    training_profile_count: int = 0


class ICPAgent(BaseAgent):
    agent_name = "icp_agent"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._training_sets: dict[str, list[ICPProfile]] = {}

    async def train(self, *, org_id: str, profiles: list[dict[str, Any]]) -> dict[str, Any]:
        parsed = [ICPProfile(text=self._profile_text(profile), label=profile.get("label"), metadata=profile) for profile in profiles]
        if len(parsed) < 3:
            return {
                "status": "needs_more_profiles",
                "trained_count": len(parsed),
                "minimum_required": 3,
                "collection": f"icp_profiles_{org_id}",
            }
        self._training_sets[org_id] = parsed
        return {
            "status": "trained",
            "trained_count": len(parsed),
            "collection": f"icp_profiles_{org_id}",
        }

    async def score(
        self,
        *,
        org_id: str,
        contact_profile: dict[str, Any],
        similar_profiles: list[dict[str, Any]] | None = None,
    ) -> ICPScoreResult:
        training = self._training_sets.get(org_id, [])
        if not training:
            return self.fallback_result(contact_profile=contact_profile, training_profiles=[], reason="training required")

        context = self._build_scoring_context(contact_profile=contact_profile, training_profiles=training, similar_profiles=similar_profiles)
        system_prompt = load_prompt_template("icp_scoring", "You are an ICP scoring agent.")
        def fallback() -> ICPScoreResult:
            return self.fallback_result(contact_profile=contact_profile, training_profiles=training, reason="llm fallback")
        payload = await self.call_llm_json(system_prompt=system_prompt, user_prompt=context, fallback=fallback)

        score = payload.get("score")
        if score is not None:
            score = max(0.0, min(1.0, float(score)))
        return ICPScoreResult(
            score=score,
            explanation=payload.get("explanation", "ICP score generated successfully."),
            fit_signals=list(payload.get("fit_signals", [])),
            gap_signals=list(payload.get("gap_signals", [])),
            fallback_used=False,
            training_profile_count=len(training),
        )

    def fallback_result(
        self,
        *,
        contact_profile: dict[str, Any],
        training_profiles: list[ICPProfile],
        reason: str,
    ) -> ICPScoreResult:
        contact_text = self._profile_text(contact_profile)
        similarities = [_word_overlap(contact_text, profile.text) for profile in training_profiles]
        score = mean(similarities) if similarities else None
        fit_signals = self._extract_signals(contact_profile, positive=True)
        gap_signals = self._extract_signals(contact_profile, positive=False)
        return ICPScoreResult(
            score=score,
            explanation=f"Fallback ICP score used because {reason}.",
            fit_signals=fit_signals,
            gap_signals=gap_signals,
            requires_training=not training_profiles,
            fallback_used=True,
            similarity_score=score,
            training_profile_count=len(training_profiles),
        )

    async def run(self, payload: dict[str, Any], context: AgentRunContext | None = None) -> Any:
        mode = str(payload.get("mode", "score")).lower()
        org_id = payload.get("org_id") or (context.org_id if context else None)
        if mode == "train":
            return await self.train(org_id=str(org_id), profiles=list(payload.get("profiles", [])))
        return await self.score(
            org_id=str(org_id),
            contact_profile=dict(payload.get("contact_profile", {})),
            similar_profiles=list(payload.get("similar_profiles", [])) or None,
        )

    def _profile_text(self, profile: dict[str, Any] | ICPProfile) -> str:
        if isinstance(profile, ICPProfile):
            return profile.text
        parts = [
            str(profile.get("name", "")),
            str(profile.get("title", "")),
            str(profile.get("company", "")),
            str(profile.get("industry", "")),
            str(profile.get("size", "")),
            str(profile.get("pain_points", "")),
            str(profile.get("notes", "")),
        ]
        return " ".join(part for part in parts if part).strip()

    def _build_scoring_context(
        self,
        *,
        contact_profile: dict[str, Any],
        training_profiles: list[ICPProfile],
        similar_profiles: list[dict[str, Any]] | None,
    ) -> str:
        similar_text = "\n".join(self._profile_text(profile) for profile in similar_profiles or [])
        training_text = "\n".join(profile.text for profile in training_profiles[:5])
        return (
            "CONTACT PROFILE:\n"
            f"{self._profile_text(contact_profile)}\n\n"
            "TRAINING EXAMPLES:\n"
            f"{training_text}\n\n"
            "SIMILAR PROFILES:\n"
            f"{similar_text}"
        )

    def _extract_signals(self, profile: dict[str, Any], *, positive: bool) -> list[str]:
        text = self._profile_text(profile).lower()
        positive_map = {
            "budget": "budget_available",
            "growth": "growth_motion",
            "security": "security_conscious",
            "hiring": "hiring_signal",
            "platform": "platform_fit",
        }
        negative_map = {
            "startup": "early_stage_risk",
            "small team": "limited_team_capacity",
            "legacy": "legacy_stack",
            "no budget": "budget_constraint",
        }
        source = positive_map if positive else negative_map
        return [signal for keyword, signal in source.items() if keyword in text]
