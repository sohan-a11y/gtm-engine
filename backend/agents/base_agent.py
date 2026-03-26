from __future__ import annotations

import asyncio
import json
import inspect
import re
import time
from dataclasses import dataclass, field
from collections.abc import Awaitable
from pathlib import Path
from typing import Any, Callable, Protocol, TypeVar, runtime_checkable


PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


class AgentError(Exception):
    """Base agent error for scaffold-level failures."""


class AgentConfigError(AgentError):
    pass


class AgentTimeoutError(AgentError):
    pass


class LLMError(AgentError):
    pass


class LLMResponseParseError(LLMError):
    pass


@dataclass(slots=True)
class AgentRunContext:
    org_id: str
    user_id: str | None = None
    trace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AgentRunResult:
    agent_name: str
    status: str
    output: Any
    raw_response: str | None = None
    latency_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@runtime_checkable
class LLMRouterProtocol(Protocol):
    def complete(self, prompt: str, *, system_prompt: str | None = None, format: str | None = None) -> Any:
        ...

    def embed(self, text: str) -> list[float]:
        ...


class LocalLLMRouter:
    """Deterministic offline router used until a real LLM adapter is wired in."""

    def complete(self, prompt: str, *, system_prompt: str | None = None, format: str | None = None) -> str:
        prompt_lower = f"{system_prompt or ''}\n{prompt}".lower()
        if "icp" in prompt_lower:
            payload = {
                "score": 0.72,
                "explanation": "Fallback ICP reasoning produced by the local router.",
                "fit_signals": ["uses-target-product", "has-budget-indicators"],
                "gap_signals": ["limited-enrichment"],
            }
        elif "outbound" in prompt_lower or "email" in prompt_lower:
            payload = {
                "variations": [
                    {
                        "subject": "Quick idea for {{company}}",
                        "body": "Hi {{first_name}}, I noticed a few signals that suggest we could help with {{pain_point}}. If useful, I can share a short walkthrough.",
                        "hook_type": "pain_point",
                        "confidence": 0.81,
                    }
                ]
            }
        elif "deal" in prompt_lower:
            payload = {
                "risk_score": 0.41,
                "risk_level": "medium",
                "risk_factors": [{"factor": "stalled_stage", "severity": "medium"}],
                "positive_signals": ["active-engagement"],
                "recommended_actions": [
                    {"action": "check_in", "owner": "AE", "urgency": "this_week"}
                ],
                "deal_summary": "The deal is progressing with some risk from stage stagnation. A proactive check-in should reduce uncertainty.",
            }
        elif "retention" in prompt_lower or "churn" in prompt_lower:
            payload = {
                "health_score": 0.68,
                "health_state": "Stable",
                "churn_driver": "low_usage",
                "playbook": "customer_success_outreach",
                "renewal_probability": 0.74,
                "state_transition": None,
                "alert_required": False,
            }
        else:
            payload = {"result": "ok"}
        return json.dumps(payload)

    def embed(self, text: str) -> list[float]:
        seed = sum(ord(ch) for ch in text)
        return [round(((seed + index * 17) % 1000) / 1000.0, 3) for index in range(16)]


def load_prompt_template(name: str, default: str = "") -> str:
    path = PROMPT_DIR / f"{name}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return default


def strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _word_overlap(left: str, right: str) -> float:
    left_words = {word for word in re.findall(r"[a-z0-9]+", left.lower()) if len(word) > 2}
    right_words = {word for word in re.findall(r"[a-z0-9]+", right.lower()) if len(word) > 2}
    if not left_words or not right_words:
        return 0.0
    return len(left_words & right_words) / max(len(left_words | right_words), 1)


T = TypeVar("T")
AuditSink = Callable[[dict[str, Any]], None | Awaitable[None]]


class BaseAgent:
    agent_name = "base_agent"

    def __init__(
        self,
        *,
        llm_router: LLMRouterProtocol | None = None,
        timeout_seconds: int = 300,
        audit_sink: AuditSink | None = None,
    ) -> None:
        self.llm_router = llm_router or LocalLLMRouter()
        self.timeout_seconds = timeout_seconds
        self.audit_sink = audit_sink

    async def run(self, payload: dict[str, Any], context: AgentRunContext | None = None) -> Any:
        raise NotImplementedError

    async def run_with_audit(self, payload: dict[str, Any], context: AgentRunContext | None = None) -> AgentRunResult:
        started = time.perf_counter()
        try:
            output = await asyncio.wait_for(self.run(payload, context), timeout=self.timeout_seconds)
            raw_response = json.dumps(output, default=str)
            result = AgentRunResult(
                agent_name=self.agent_name,
                status="success",
                output=output,
                raw_response=raw_response,
                latency_ms=int((time.perf_counter() - started) * 1000),
                metadata={"org_id": context.org_id if context else None} if context else {},
            )
            await self._emit_audit(result, payload, context)
            return result
        except asyncio.TimeoutError as exc:
            result = AgentRunResult(
                agent_name=self.agent_name,
                status="timeout",
                output=None,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc),
            )
            await self._emit_audit(result, payload, context)
            raise AgentTimeoutError(f"{self.agent_name} timed out") from exc

    async def call_llm_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        fallback: Callable[[], Any] | None = None,
        attempts: int = 3,
    ) -> Any:
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            response = await self._maybe_await(
                self.llm_router.complete(
                    user_prompt,
                    system_prompt=system_prompt,
                    format="json",
                )
            )
            raw = response if isinstance(response, str) else json.dumps(response, default=str)
            try:
                return json.loads(strip_markdown_fences(raw))
            except json.JSONDecodeError as exc:
                last_error = exc
                user_prompt = f"{user_prompt}\n\nReturn only valid JSON. Previous parse error: {exc}"
        if fallback is not None:
            return fallback()
        raise LLMResponseParseError(str(last_error) if last_error else "Unknown JSON parse failure")

    async def embed_text(self, text: str) -> list[float]:
        embedding = await self._maybe_await(self.llm_router.embed(text))
        return list(embedding)

    async def _emit_audit(self, result: AgentRunResult, payload: dict[str, Any], context: AgentRunContext | None) -> None:
        if self.audit_sink is None:
            return
        record = {
            "agent_name": self.agent_name,
            "payload": payload,
            "context": context.__dict__ if context else {},
            "status": result.status,
            "latency_ms": result.latency_ms,
            "error": result.error,
        }
        maybe = self.audit_sink(record)
        if asyncio.iscoroutine(maybe):
            await maybe

    async def _maybe_await(self, value: Any) -> Any:
        if inspect.isawaitable(value):
            return await value
        return value
