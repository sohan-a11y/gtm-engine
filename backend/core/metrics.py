from __future__ import annotations

from typing import Any

try:  # pragma: no cover - dependency availability is environment dependent
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
except Exception:  # pragma: no cover
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    class _NoOpMetric:
        def labels(self, *_args: Any, **_kwargs: Any) -> "_NoOpMetric":
            return self

        def inc(self, *_args: Any, **_kwargs: Any) -> None:
            return None

        def observe(self, *_args: Any, **_kwargs: Any) -> None:
            return None

        def set(self, *_args: Any, **_kwargs: Any) -> None:
            return None

    def Counter(*_args: Any, **_kwargs: Any) -> _NoOpMetric:  # type: ignore[misc]
        return _NoOpMetric()

    def Gauge(*_args: Any, **_kwargs: Any) -> _NoOpMetric:  # type: ignore[misc]
        return _NoOpMetric()

    def Histogram(*_args: Any, **_kwargs: Any) -> _NoOpMetric:  # type: ignore[misc]
        return _NoOpMetric()

    def generate_latest() -> bytes:  # type: ignore[misc]
        return b""


api_requests_total = Counter("gtm_api_requests_total", "API requests", ["method", "endpoint", "status"])
api_request_latency_seconds = Histogram(
    "gtm_api_request_latency_seconds",
    "API request latency",
    ["method", "endpoint"],
)
agent_runs_total = Counter("gtm_agent_runs_total", "Agent runs", ["agent", "status"])
agent_run_latency_seconds = Histogram("gtm_agent_run_latency_seconds", "Agent latency", ["agent"])
llm_calls_total = Counter("gtm_llm_calls_total", "LLM calls", ["provider", "model"])
llm_tokens_total = Counter("gtm_llm_tokens_total", "LLM tokens", ["provider", "kind"])
llm_cost_usd_total = Counter("gtm_llm_cost_usd_total", "LLM cost", ["provider"])
active_agent_runs = Gauge("gtm_active_agent_runs", "Active agent runs", ["agent"])
business_events_total = Counter("gtm_business_events_total", "Business events", ["name", "org_id"])


def record_api_request(method: str, endpoint: str, status: int, latency_seconds: float) -> None:
    api_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    api_request_latency_seconds.labels(method=method, endpoint=endpoint).observe(latency_seconds)


def record_agent_run(agent: str, status: str, latency_seconds: float | None = None) -> None:
    agent_runs_total.labels(agent=agent, status=status).inc()
    if latency_seconds is not None:
        agent_run_latency_seconds.labels(agent=agent).observe(latency_seconds)


def record_llm_call(
    provider: str,
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost_usd: float = 0.0,
) -> None:
    llm_calls_total.labels(provider=provider, model=model).inc()
    llm_tokens_total.labels(provider=provider, kind="prompt").inc(prompt_tokens)
    llm_tokens_total.labels(provider=provider, kind="completion").inc(completion_tokens)
    llm_cost_usd_total.labels(provider=provider).inc(cost_usd)


def record_business_event(name: str, org_id: str) -> None:
    business_events_total.labels(name=name, org_id=org_id).inc()


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST

