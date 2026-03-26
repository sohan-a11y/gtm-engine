from __future__ import annotations

import asyncio
import tempfile
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.db.models import Base, Contact, Organization  # noqa: E402
from backend.agents.base_agent import LocalLLMRouter  # noqa: E402


@pytest.fixture()
def temp_db_url() -> str:
    directory = Path(tempfile.mkdtemp(prefix="gtm-engine-tests-"))
    return f"sqlite+aiosqlite:///{directory / 'test.db'}"


@pytest.fixture()
def session_factory(temp_db_url: str):
    engine = create_async_engine(temp_db_url, future=True)

    async def prepare() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(prepare())
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory

    async def cleanup() -> None:
        await engine.dispose()

    asyncio.run(cleanup())


@pytest.fixture()
def org_id() -> str:
    return str(uuid4())


@pytest.fixture()
def sample_org() -> Organization:
    return Organization(id=uuid4(), name="Acme", slug="acme")


@pytest.fixture()
def sample_contact(org_id: str) -> Contact:
    return Contact(
        id=uuid4(),
        org_id=org_id,
        email="jane@example.com",
        first_name="Jane",
        last_name="Doe",
        title="VP Revenue",
        status="new",
    )


@pytest.fixture()
def llm_router() -> LocalLLMRouter:
    return LocalLLMRouter()
