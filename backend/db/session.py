from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


DEFAULT_SQLITE_URL = "sqlite+aiosqlite:///./gtm_engine.db"


def get_database_url(default: str | None = None) -> str:
    return os.getenv("DATABASE_URL") or default or DEFAULT_SQLITE_URL


def _engine_kwargs(database_url: str) -> dict[str, object]:
    url = make_url(database_url)
    if url.drivername.startswith("sqlite"):
        return {"echo": False, "future": True}
    return {
        "echo": False,
        "future": True,
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }


def build_async_engine(database_url: str | None = None) -> AsyncEngine:
    url = database_url or get_database_url()
    return create_async_engine(url, **_engine_kwargs(url))


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
