from __future__ import annotations

import asyncio
from uuid import uuid4

from backend.db.models import Base, Campaign, Company, Contact, Organization


def test_metadata_contains_core_tables():
    table_names = set(Base.metadata.tables.keys())
    for expected in {"organizations", "users", "companies", "contacts", "deals", "campaigns"}:
        assert expected in table_names


def test_sqlite_metadata_round_trip(session_factory):
    async def scenario():
        async with session_factory() as session:
            org = Organization(id=uuid4(), name="Org", slug="org")
            company = Company(org_id=org.id, name="Acme", domain="acme.com")
            contact = Contact(org_id=org.id, email="jane@acme.com", first_name="Jane", last_name="Doe")
            campaign = Campaign(org_id=org.id, name="Pilot", status="active")
            session.add_all([org, company, contact, campaign])
            await session.flush()
            assert org.id is not None
            assert company.org_id == org.id
            assert contact.email == "jane@acme.com"

    asyncio.run(scenario())
