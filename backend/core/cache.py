from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any

try:  # pragma: no cover - optional dependency path
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore[assignment]


class CacheBackend:
    async def get(self, key: str) -> Any:  # pragma: no cover - interface only
        raise NotImplementedError

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:  # pragma: no cover
        raise NotImplementedError

    async def delete(self, key: str) -> None:  # pragma: no cover - interface only
        raise NotImplementedError

    async def increment(self, key: str, ttl_seconds: int | None = None) -> int:  # pragma: no cover
        raise NotImplementedError


@dataclass(slots=True)
class InMemoryCache(CacheBackend):
    _values: dict[str, tuple[Any, float | None]]
    _lock: asyncio.Lock = None  # type: ignore[assignment]

    def __init__(self) -> None:
        self._values = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any:
        async with self._lock:
            entry = self._values.get(key)
            if not entry:
                return None
            value, expires_at = entry
            if expires_at is not None and expires_at < time.time():
                self._values.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        async with self._lock:
            expires_at = time.time() + ttl_seconds if ttl_seconds else None
            self._values[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._values.pop(key, None)

    async def increment(self, key: str, ttl_seconds: int | None = None) -> int:
        async with self._lock:
            current = 0
            entry = self._values.get(key)
            if entry:
                value, expires_at = entry
                if expires_at is None or expires_at >= time.time():
                    try:
                        current = int(value)
                    except Exception:
                        current = 0
            current += 1
            expires_at = time.time() + ttl_seconds if ttl_seconds else None
            self._values[key] = (current, expires_at)
            return current


@dataclass(slots=True)
class RedisCache(CacheBackend):
    client: Any

    @classmethod
    def from_url(cls, url: str) -> "RedisCache":
        if redis is None:
            raise RuntimeError("redis package not available")
        return cls(client=redis.from_url(url, decode_responses=True))

    async def get(self, key: str) -> Any:
        raw = await self.client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        raw = json.dumps(value, default=str)
        await self.client.set(key, raw, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def increment(self, key: str, ttl_seconds: int | None = None) -> int:
        value = await self.client.incr(key)
        if ttl_seconds:
            await self.client.expire(key, ttl_seconds)
        return int(value)


def build_cache_backend(redis_url: str | None = None) -> CacheBackend:
    if redis_url and redis is not None:
        try:
            return RedisCache.from_url(redis_url)
        except Exception:
            pass
    return InMemoryCache()


def cache_key(*parts: str) -> str:
    return ":".join(part.strip(":") for part in parts if part)
