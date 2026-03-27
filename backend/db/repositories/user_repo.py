from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base_repository import BaseRepository
from backend.db.models import Organization, User


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, *, org_id: UUID, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.org_id == org_id, User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_email_any_org(self, *, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Organization)

    async def get_by_slug(self, *, slug: str) -> Organization | None:
        result = await self.session.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_org(self, *, name: str, slug: str, plan: str = "free") -> Organization:
        org = Organization(name=name, slug=slug, plan=plan)
        self.session.add(org)
        await self.session.flush()
        return org
