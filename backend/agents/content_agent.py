from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from backend.agents.base_agent import AgentRunContext, BaseAgent, load_prompt_template


ContentMode = Literal["SEO_BLOG_POST", "EMAIL_SEQUENCE", "LINKEDIN_POST"]


@dataclass(slots=True)
class ContentDraft:
    mode: str
    title: str
    body: str
    quality_flags: list[str] = field(default_factory=list)
    status: str = "draft"


class ContentAgent(BaseAgent):
    agent_name = "content_agent"

    async def generate(
        self,
        *,
        mode: ContentMode,
        topic: str,
        brand_voice: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ContentDraft:
        prompt_name = "content_generation"
        prompt = load_prompt_template(prompt_name, "Generate marketing content.")
        user_prompt = self._build_prompt(mode=mode, topic=topic, brand_voice=brand_voice, context=context)
        payload = await self.call_llm_json(system_prompt=prompt, user_prompt=user_prompt, fallback=lambda: self._fallback(mode, topic, brand_voice, context))
        draft = ContentDraft(
            mode=mode,
            title=str(payload.get("title", topic)).strip(),
            body=str(payload.get("body", "")).strip(),
            quality_flags=list(payload.get("quality_flags", [])),
            status=str(payload.get("status", "draft")),
        )
        return self._auto_flag(draft)

    async def generate_blog_post(self, *, topic: str, brand_voice: str | None = None, context: dict[str, Any] | None = None) -> ContentDraft:
        return await self.generate(mode="SEO_BLOG_POST", topic=topic, brand_voice=brand_voice, context=context)

    async def generate_email_sequence(self, *, topic: str, brand_voice: str | None = None, context: dict[str, Any] | None = None) -> ContentDraft:
        return await self.generate(mode="EMAIL_SEQUENCE", topic=topic, brand_voice=brand_voice, context=context)

    async def generate_linkedin_post(self, *, topic: str, brand_voice: str | None = None, context: dict[str, Any] | None = None) -> ContentDraft:
        return await self.generate(mode="LINKEDIN_POST", topic=topic, brand_voice=brand_voice, context=context)

    async def run(self, payload: dict[str, Any], context: AgentRunContext | None = None) -> Any:
        return await self.generate(
            mode=str(payload.get("mode", "SEO_BLOG_POST")),
            topic=str(payload.get("topic", "GTM strategy")),
            brand_voice=payload.get("brand_voice"),
            context=dict(payload.get("context", {})) or None,
        )

    def _build_prompt(
        self,
        *,
        mode: ContentMode,
        topic: str,
        brand_voice: str | None,
        context: dict[str, Any] | None,
    ) -> str:
        return (
            f"MODE: {mode}\n"
            f"TOPIC: {topic}\n"
            f"BRAND_VOICE: {brand_voice or ''}\n"
            f"CONTEXT: {context or {}}"
        )

    def _fallback(
        self,
        mode: ContentMode,
        topic: str,
        brand_voice: str | None,
        context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        opening = f"{topic} is changing quickly, and teams need a practical way to stay ahead."
        if mode == "EMAIL_SEQUENCE":
            body = f"{opening} This sequence should outline a clear value proposition and end with a direct CTA."
        elif mode == "LINKEDIN_POST":
            body = f"{opening} Here is a concise perspective, a concrete lesson, and a question to invite discussion."
        else:
            body = (
                f"{opening} This draft should balance search intent, product education, and a simple next step."
            )
        return {"title": topic, "body": body, "quality_flags": [], "status": "draft"}

    def _auto_flag(self, draft: ContentDraft) -> ContentDraft:
        flags = set(draft.quality_flags)
        words = len(draft.body.split())
        if words > 900:
            flags.add("over_length")
        if "?" not in draft.body:
            flags.add("weak_cta")
        if any(term in draft.body.lower() for term in ["buy now", "best-in-class", "revolutionary"]):
            flags.add("too_salesy")
        if not any(keyword in draft.body.lower() for keyword in ["because", "why", "how", "for example"]):
            flags.add("missing_hook")
        draft.quality_flags = sorted(flags)
        return draft
