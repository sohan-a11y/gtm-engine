from __future__ import annotations

import json
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.leads import LeadCreate, LeadImportResult, LeadResponse, LeadUpdate
from backend.core.context_builder import ContextBuilder, build_context_builder
from backend.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from backend.core.llm_router import LLMRouter, build_llm_router
from backend.core.metrics import record_business_event
from backend.core.prompt_manager import PromptManager, build_prompt_manager
from backend.db.models import Contact
from backend.db.repositories.contact_repo import ContactRepository

from .base import BaseService


def _contact_to_lead(contact: Contact) -> LeadResponse:
    ed = contact.enrichment_data or {}
    return LeadResponse(
        id=str(contact.id),
        org_id=str(contact.org_id),
        email=contact.email,
        first_name=contact.first_name or None,
        last_name=contact.last_name or None,
        company_name=ed.get("company_name"),
        title=contact.title,
        source=ed.get("source", "manual"),
        notes=ed.get("notes"),
        metadata=ed.get("metadata", {}),
        status=contact.status,
        icp_score=contact.icp_score,
        icp_score_reason=contact.icp_score_reason,
        fit_signals=contact.fit_signals or [],
        gap_signals=contact.gap_signals or [],
        enrichment_status=contact.enrichment_status,
        enrichment_data=ed,
        created_at=contact.created_at,
        updated_at=contact.updated_at,
    )


def _lead_create_to_data(org_id: str, data: LeadCreate) -> dict:
    enrichment_data: dict = {}
    if data.company_name is not None:
        enrichment_data["company_name"] = data.company_name
    enrichment_data["source"] = data.source
    if data.notes is not None:
        enrichment_data["notes"] = data.notes
    if data.metadata:
        enrichment_data["metadata"] = data.metadata
    return {
        "org_id": UUID(org_id),
        "email": data.email,
        "first_name": data.first_name or "",
        "last_name": data.last_name or "",
        "title": data.title,
        "enrichment_data": enrichment_data,
        "status": "new",
        "enrichment_status": "pending",
    }


@dataclass(slots=True)
class LeadService(BaseService):
    llm_router: LLMRouter = field(default_factory=build_llm_router)
    context_builder: ContextBuilder = field(default_factory=build_context_builder)
    prompt_manager: PromptManager = field(default_factory=build_prompt_manager)

    async def create_lead(self, org_id: str, data: LeadCreate, *, session: AsyncSession) -> LeadResponse:
        repo = ContactRepository(session)
        try:
            existing = await repo.get_by_email(org_id=UUID(org_id), email=data.email.lower())
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if existing is not None:
            raise ConflictError("Lead already exists")
        contact_data = _lead_create_to_data(org_id, data)
        contact_data["email"] = contact_data["email"].lower()
        try:
            contact = await repo.create(org_id=UUID(org_id), data=contact_data)
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        self.state.publish_event("lead_created", {"lead_id": str(contact.id), "org_id": org_id})
        record_business_event("lead_created", org_id)
        return _contact_to_lead(contact)

    async def list_leads(self, org_id: str, *, session: AsyncSession) -> list[LeadResponse]:
        repo = ContactRepository(session)
        try:
            contacts = await repo.list(org_id=UUID(org_id))
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return [_contact_to_lead(c) for c in contacts]

    async def get_lead(self, org_id: str, lead_id: str, *, session: AsyncSession) -> LeadResponse:
        repo = ContactRepository(session)
        try:
            contact = await repo.get(org_id=UUID(org_id), object_id=UUID(lead_id))
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if contact is None:
            raise NotFoundError("Lead not found")
        return _contact_to_lead(contact)

    async def update_lead(self, org_id: str, lead_id: str, data: LeadUpdate, *, session: AsyncSession) -> LeadResponse:
        repo = ContactRepository(session)
        try:
            contact = await repo.get(org_id=UUID(org_id), object_id=UUID(lead_id))
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if contact is None:
            raise NotFoundError("Lead not found")
        updates = data.model_dump(exclude_none=True)
        # Fields that live in enrichment_data
        ed = dict(contact.enrichment_data or {})
        for key in ("company_name", "source", "notes", "metadata"):
            if key in updates:
                ed[key] = updates.pop(key)
        if ed != (contact.enrichment_data or {}):
            updates["enrichment_data"] = ed
        try:
            updated = await repo.update_by_id(org_id=UUID(org_id), object_id=UUID(lead_id), data=updates)
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if updated is None:
            raise NotFoundError("Lead not found")
        self.state.publish_event("lead_updated", {"lead_id": lead_id, "org_id": org_id})
        return _contact_to_lead(updated)

    async def import_leads(self, org_id: str, rows: list[LeadCreate], *, session: AsyncSession) -> LeadImportResult:
        imported = skipped = duplicates = errors = 0
        for row in rows:
            try:
                await self.create_lead(org_id, row, session=session)
                imported += 1
            except ConflictError:
                duplicates += 1
            except Exception:
                errors += 1
                skipped += 1
        return LeadImportResult(imported=imported, skipped=skipped, duplicates=duplicates, errors=errors)

    async def score_lead(self, org_id: str, lead_id: str, *, session: AsyncSession) -> LeadResponse:
        lead = await self.get_lead(org_id, lead_id, session=session)
        context = self.context_builder.build_lead_context(lead.model_dump())
        response = await self.llm_router.complete(
            system=self.prompt_manager.load("icp_scoring"),
            user=context,
            format="json",
            metadata={"org_id": org_id, "agent_name": "icp_agent"},
        )
        payload = json.loads(response.content)
        repo = ContactRepository(session)
        score = max(0.0, min(1.0, float(payload.get("score", 0.0))))
        reason = payload.get("explanation")
        fit_signals = list(payload.get("fit_signals", []))
        gap_signals = list(payload.get("gap_signals", []))
        try:
            contact = await repo.mark_scored(
                org_id=UUID(org_id),
                contact_id=UUID(lead_id),
                score=score,
                reason=reason,
                fit_signals=fit_signals,
                gap_signals=gap_signals,
            )
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if contact is None:
            raise NotFoundError("Lead not found")
        self.state.publish_event("lead_scored", {"lead_id": lead_id, "org_id": org_id, "score": score})
        return _contact_to_lead(contact)
