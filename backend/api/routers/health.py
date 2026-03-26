from __future__ import annotations

import os

import httpx
from fastapi import APIRouter

try:  # pragma: no cover - optional dependency path
    import asyncpg
except Exception:  # pragma: no cover
    asyncpg = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency path
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore[assignment]

router = APIRouter(tags=["health"])


async def _check_postgres() -> str:
    dsn = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
    if asyncpg is None:
        return "disconnected"
    if not dsn:
        return "disconnected"
    try:
        conn = await asyncpg.connect(dsn=dsn, timeout=5)
        try:
            await conn.execute("SELECT 1")
        finally:
            await conn.close()
        return "connected"
    except Exception:
        return "disconnected"


async def _check_redis() -> str:
    url = os.getenv("REDIS_URL")
    if redis is None:
        return "disconnected"
    if not url:
        return "disconnected"
    client = redis.from_url(url, decode_responses=True)
    try:
        await client.ping()
        return "connected"
    except Exception:
        return "disconnected"
    finally:
        await client.aclose()


async def _check_qdrant() -> str:
    url = os.getenv("QDRANT_URL")
    if not url:
        return "disconnected"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url.rstrip('/')}/healthz")
            if response.status_code < 500:
                return "connected"
            return "disconnected"
    except Exception:
        return "disconnected"


@router.get("/health")
async def health_check() -> dict[str, str]:
    postgres = await _check_postgres()
    redis_status = await _check_redis()
    qdrant = await _check_qdrant()
    overall = "ok" if all(part == "connected" for part in (postgres, redis_status, qdrant)) else "degraded"
    return {"status": overall, "postgres": postgres, "redis": redis_status, "qdrant": qdrant}
