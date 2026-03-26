from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Any

DEFAULT_PROMPTS: dict[str, str] = {
    "icp_scoring": "Score the lead profile and return JSON with score, explanation, fit_signals, and gap_signals.",
    "outbound_personalization": (
        "Write three short outbound email variations. Return JSON with subject, body, hook_type, confidence."
    ),
    "content_generation": "Create GTM content assets with structured outputs.",
    "deal_intelligence": "Analyze a sales call transcript and return risk signals and next steps.",
    "retention_analysis": "Assess customer health and churn risk with actionable recommendations.",
}


class _SafeDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass(slots=True)
class PromptManager:
    prompt_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "prompts")

    def load(self, prompt_name: str) -> str:
        path = self.prompt_dir / f"{prompt_name}.txt"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return DEFAULT_PROMPTS.get(prompt_name, "")

    def render(self, prompt_name: str, **variables: Any) -> str:
        template = self.load(prompt_name)
        if not template:
            return ""
        if "{" in template:
            return template.format_map(_SafeDict(**variables))
        return Template(template).safe_substitute(**variables)


def build_prompt_manager() -> PromptManager:
    return PromptManager()

