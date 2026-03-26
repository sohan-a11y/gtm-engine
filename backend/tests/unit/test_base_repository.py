from __future__ import annotations

import asyncio
from uuid import uuid4

from backend.db.models import Contact, Organization
from backend.db.repositories.contact_repo import ContactRepository


def test_base_repository_scopes_by_org(session_factory):
    async def scenario():
        async with session_factory() as session:
            org_a = Organization(id=uuid4(), name="Org A", slug="org-a")
            org_b = Organization(id=uuid4(), name="Org B", slug="org-b")
            session.add_all([org_a, org_b])
            await session.flush()

            contact_a = Contact(org_id=org_a.id, email="a@example.com", first_name="A", last_name="One")
            contact_b = Contact(org_id=org_b.id, email="b@example.com", first_name="B", last_name="Two")
            session.add_all([contact_a, contact_b])
            await session.flush()

            repo = ContactRepository(session)
            assert await repo.get_by_email(org_id=org_a.id, email="a@example.com") is not None
            assert await repo.get_by_email(org_id=org_a.id, email="b@example.com") is None

    asyncio.run(scenario())


def test_base_repository_strips_tenant_fields(session_factory):
    async def scenario():
        async with session_factory() as session:
            org = Organization(id=uuid4(), name="Org", slug="org")
            session.add(org)
            await session.flush()

            repo = ContactRepository(session)
            contact = await repo.create(
                org_id=org.id,
                data={"email": "c@example.com", "first_name": "C", "last_name": "Example", "org_id": uuid4()},
            )
            await session.flush()

            assert contact.org_id == org.id
            assert contact.email == "c@example.com"

    asyncio.run(scenario())
