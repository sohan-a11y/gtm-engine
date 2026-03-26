from __future__ import annotations

import time
from dataclasses import dataclass

from .cache import CacheBackend, build_cache_backend, cache_key


@dataclass(slots=True)
class RateLimitRule:
    limit: int
    window_seconds: int


@dataclass(slots=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_at: float
    limit: int
    window_seconds: int


DEFAULT_RATE_LIMITS: dict[str, RateLimitRule] = {
    "public_login": RateLimitRule(limit=20, window_seconds=60),
    "authenticated_api": RateLimitRule(limit=100, window_seconds=60),
    "agent_trigger": RateLimitRule(limit=10, window_seconds=60),
}


class RateLimiter:
    def __init__(self, cache: CacheBackend | None = None) -> None:
        self.cache = cache or build_cache_backend()

    async def check(self, subject: str, rule_name: str, namespace: str = "") -> RateLimitResult:
        rule = DEFAULT_RATE_LIMITS[rule_name]
        bucket = cache_key("rate", namespace, rule_name, subject)
        count = await self.cache.increment(bucket, ttl_seconds=rule.window_seconds)
        reset_at = time.time() + rule.window_seconds
        remaining = max(rule.limit - count, 0)
        return RateLimitResult(
            allowed=count <= rule.limit,
            remaining=remaining,
            reset_at=reset_at,
            limit=rule.limit,
            window_seconds=rule.window_seconds,
        )


def build_rate_limiter(cache: CacheBackend | None = None) -> RateLimiter:
    return RateLimiter(cache=cache)

