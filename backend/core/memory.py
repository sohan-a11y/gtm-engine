from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .cache import CacheBackend, build_cache_backend, cache_key


@dataclass(slots=True)
class MemoryItem:
    key: str
    value: Any
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MemoryManager:
    cache: CacheBackend = field(default_factory=build_cache_backend)
    semantic_store: dict[str, list[MemoryItem]] = field(default_factory=dict)
    long_term_store: dict[str, list[MemoryItem]] = field(default_factory=dict)

    async def remember(self, org_id: str, namespace: str, key: str, value: Any) -> None:
        cache_namespace = cache_key("memory", org_id, namespace, key)
        await self.cache.set(cache_namespace, value, ttl_seconds=3600)
        item = MemoryItem(key=key, value=value)
        self.semantic_store.setdefault(cache_key(org_id, namespace), []).append(item)
        self.long_term_store.setdefault(org_id, []).append(item)

    async def recall(self, org_id: str, namespace: str, key: str) -> Any:
        cache_namespace = cache_key("memory", org_id, namespace, key)
        cached = await self.cache.get(cache_namespace)
        if cached is not None:
            return cached
        for item in self.semantic_store.get(cache_key(org_id, namespace), []):
            if item.key == key:
                return item.value
        return None

    async def search(self, org_id: str, query: str) -> list[dict[str, Any]]:
        results = []
        for item in self.long_term_store.get(org_id, []):
            haystack = json.dumps(item.value, default=str).lower()
            score = sum(token in haystack for token in query.lower().split())
            if score:
                results.append({"key": item.key, "value": item.value, "score": score})
        return sorted(results, key=lambda record: record["score"], reverse=True)


def build_memory_manager() -> MemoryManager:
    return MemoryManager()

