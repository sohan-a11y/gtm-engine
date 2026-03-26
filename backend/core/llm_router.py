from __future__ import annotations

import asyncio
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any

from .audit_logger import AuditLogger, build_audit_logger
from .exceptions import LLMError
from .metrics import record_llm_call
from .prompt_manager import PromptManager, build_prompt_manager

try:  # pragma: no cover - optional provider path
    from litellm import acompletion  # type: ignore
except Exception:  # pragma: no cover
    acompletion = None  # type: ignore[assignment]


@dataclass(slots=True)
class LLMResponse:
    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0


@dataclass(slots=True)
class LLMRouter:
    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "mock"))
    model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "mock-model"))
    api_key: str | None = field(default_factory=lambda: os.getenv("LLM_API_KEY"))
    prompt_manager: PromptManager = field(default_factory=build_prompt_manager)
    audit_logger: AuditLogger = field(default_factory=build_audit_logger)

    async def complete(
        self,
        *,
        system: str,
        user: str,
        format: str = "text",
        temperature: float = 0.2,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        if self.provider != "mock" and acompletion is not None and self.api_key:
            try:
                response = await acompletion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=temperature,
                )
                content = response.choices[0].message.content or ""
                usage = getattr(response, "usage", None)
                prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
                completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
                cost_usd = float(getattr(response, "cost", 0.0) or 0.0)
                record_llm_call(self.provider, self.model, prompt_tokens, completion_tokens, cost_usd)
                self.audit_logger.log_agent_run(
                    org_id=str(metadata.get("org_id")) if metadata else "unknown",
                    agent_name=str(metadata.get("agent_name")) if metadata else "llm",
                    prompt=system + "\n" + user,
                    response=content,
                    metadata=metadata or {},
                )
                return LLMResponse(
                    content=content,
                    provider=self.provider,
                    model=self.model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost_usd=cost_usd,
                )
            except Exception as exc:  # pragma: no cover - external path
                raise LLMError(str(exc)) from exc

        content = self._fallback_complete(system=system, user=user, format=format)
        record_llm_call(self.provider, self.model, 0, 0, 0.0)
        self.audit_logger.log_agent_run(
            org_id=str(metadata.get("org_id")) if metadata else "unknown",
            agent_name=str(metadata.get("agent_name")) if metadata else "llm",
            prompt=system + "\n" + user,
            response=content,
            metadata=metadata or {},
        )
        return LLMResponse(content=content, provider=self.provider, model=self.model)

    async def embed(self, text: str) -> list[float]:
        if self.provider != "mock" and acompletion is not None and self.api_key:
            # This scaffold keeps embeddings deterministic until a real provider is wired in.
            pass
        return self._fallback_embedding(text)

    def _fallback_complete(self, *, system: str, user: str, format: str) -> str:
        digest = hashlib.sha256((system + "\n" + user).encode("utf-8")).hexdigest()
        if format == "json":
            variations = []
            for index in range(3):
                variations.append(
                    {
                        "subject": f"Scaffold follow-up {index + 1}",
                        "body": "Thanks for the context. I would love to keep the conversation going.",
                        "hook_type": "contextual",
                        "confidence": round(0.9 - index * 0.1, 2),
                    }
                )
            payload = {
                "score": round((int(digest[:4], 16) % 1000) / 1000, 3),
                "explanation": "Deterministic scaffold response generated locally.",
                "fit_signals": ["scaffold", "deterministic"],
                "gap_signals": ["llm_provider_not_configured"],
                "variations": variations,
            }
            return json.dumps(payload)
        return f"scaffold-response::{digest[:32]}"

    def _fallback_embedding(self, text: str, dimensions: int = 1536) -> list[float]:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        while len(values) < dimensions:
            for byte in seed:
                values.append(round(byte / 255.0, 6))
                if len(values) >= dimensions:
                    break
        return values


def build_llm_router() -> LLMRouter:
    return LLMRouter()
