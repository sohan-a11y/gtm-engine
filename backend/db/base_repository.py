from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


ModelT = TypeVar("ModelT")


def _coerce_mapping(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, Mapping):
        return dict(payload)
    dump = getattr(payload, "model_dump", None)
    if callable(dump):
        return dict(dump())
    if hasattr(payload, "__dict__"):
        return {k: v for k, v in vars(payload).items() if not k.startswith("_")}
    raise TypeError(f"Unsupported payload type: {type(payload)!r}")


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession, model: type[ModelT] | None = None) -> None:
        self.session = session
        if model is not None:
            self.model = model
        self._tenant_scoped = hasattr(self.model, "org_id")

    def _tenant_clause(self, org_id: UUID | None):
        if self._tenant_scoped and org_id is None:
            raise ValueError("org_id is required for tenant-scoped repositories")
        if self._tenant_scoped:
            return self.model.org_id == org_id  # type: ignore[attr-defined]
        return None

    async def get(self, *, org_id: UUID | None, object_id: UUID) -> ModelT | None:
        stmt = select(self.model).where(self.model.id == object_id)  # type: ignore[attr-defined]
        clause = self._tenant_clause(org_id)
        if clause is not None:
            stmt = stmt.where(clause)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        org_id: UUID | None,
        filters: Mapping[str, Any] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ModelT]:
        stmt = select(self.model)
        clause = self._tenant_clause(org_id)
        if clause is not None:
            stmt = stmt.where(clause)
        for key, value in (filters or {}).items():
            if value is not None and hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt.limit(limit).offset(offset))
        return result.scalars().all()

    async def create(self, *, org_id: UUID | None, data: Any) -> ModelT:
        payload = _coerce_mapping(data)
        payload.pop("id", None)
        if self._tenant_scoped:
            payload.pop("org_id", None)
            payload["org_id"] = org_id
        obj = self.model(**payload)  # type: ignore[call-arg]
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update_by_id(self, *, org_id: UUID | None, object_id: UUID, data: Any) -> ModelT | None:
        obj = await self.get(org_id=org_id, object_id=object_id)
        if obj is None:
            return None
        payload = _coerce_mapping(data)
        payload.pop("id", None)
        payload.pop("org_id", None)
        for key, value in payload.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self.session.flush()
        return obj

    async def delete_by_id(self, *, org_id: UUID | None, object_id: UUID) -> bool:
        obj = await self.get(org_id=org_id, object_id=object_id)
        if obj is None:
            return False
        await self.session.delete(obj)  # type: ignore[arg-type]
        await self.session.flush()
        return True

    async def exists(self, *, org_id: UUID | None, filters: Mapping[str, Any]) -> bool:
        stmt = select(self.model.id)  # type: ignore[attr-defined]
        clause = self._tenant_clause(org_id)
        if clause is not None:
            stmt = stmt.where(clause)
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None
