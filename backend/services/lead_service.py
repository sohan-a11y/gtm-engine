from __future__ import annotations

import json
from dataclasses import dataclass, field

from backend.api.schemas.leads import LeadCreate, LeadImportResult, LeadResponse, LeadUpdate
from backend.core.context_builder import ContextBuilder, build_context_builder
from backend.core.exceptions import ConflictError, NotFoundError
from backend.core.llm_router import LLMRouter, build_llm_router
from backend.core.metrics import record_business_event
from backend.core.prompt_manager import PromptManager, build_prompt_manager

from .base import BaseService
from .state import generate_id, utc_now


@dataclass(slots=True)
class LeadService(BaseService):
    llm_router: LLMRouter = field(default_factory=build_llm_router)
    context_builder: ContextBuilder = field(default_factory=build_context_builder)
    prompt_manager: PromptManager = field(default_factory=build_prompt_manager)

    async def create_lead(self, org_id: str, data: LeadCreate) -> LeadResponse:
        if any(lead["org_id"] == org_id and lead["email"].lower() == data.email.lower() for lead in self.state.leads.values()):
            raise ConflictError("Lead already exists")
        lead_id = generate_id("lead")
        now = utc_now()
        record = {
            "id": lead_id,
            "org_id": org_id,
            "status": "new",
            "icp_score": None,
            "icp_score_reason": None,
            "fit_signals": [],
            "gap_signals": [],
            "enrichment_status": "pending",
            "enrichment_data": {},
            "created_at": now,
            "updated_at": now,
            **data.model_dump(),
        }
        self.state.leads[lead_id] = record
        self.state.publish_event("lead_created", {"lead_id": lead_id, "org_id": org_id})
        record_business_event("lead_created", org_id)
        return LeadResponse.model_validate(record)

    async def list_leads(self, org_id: str) -> list[LeadResponse]:
        leads = [lead for lead in self.state.leads.values() if lead["org_id"] == org_id]
        return [LeadResponse.model_validate(lead) for lead in sorted(leads, key=lambda item: item["created_at"], reverse=True)]

    async def get_lead(self, org_id: str, lead_id: str) -> LeadResponse:
        lead = self.state.leads.get(lead_id)
        if not lead or lead["org_id"] != org_id:
            raise NotFoundError("Lead not found")
        return LeadResponse.model_validate(lead)

    async def update_lead(self, org_id: str, lead_id: str, data: LeadUpdate) -> LeadResponse:
        lead = self.state.leads.get(lead_id)
        if not lead or lead["org_id"] != org_id:
            raise NotFoundError("Lead not found")
        updates = data.model_dump(exclude_none=True)
        lead.update(updates)
        lead["updated_at"] = utc_now()
        self.state.publish_event("lead_updated", {"lead_id": lead_id, "org_id": org_id})
        return LeadResponse.model_validate(lead)

    async def import_leads(self, org_id: str, rows: list[LeadCreate]) -> LeadImportResult:
        imported = skipped = duplicates = errors = 0
        for row in rows:
            try:
                await self.create_lead(org_id, row)
                imported += 1
            except ConflictError:
                duplicates += 1
            except Exception:
                errors += 1
                skipped += 1
        return LeadImportResult(imported=imported, skipped=skipped, duplicates=duplicates, errors=errors)

    async def score_lead(self, org_id: str, lead_id: str) -> LeadResponse:
        lead = await self.get_lead(org_id, lead_id)
        context = self.context_builder.build_lead_context(lead.model_dump())
        response = await self.llm_router.complete(
            system=self.prompt_manager.load("icp_scoring"),
            user=context,
            format="json",
            metadata={"org_id": org_id, "agent_name": "icp_agent"},
        )
        payload = json.loads(response.content)
        stored = self.state.leads[lead_id]
        stored["icp_score"] = max(0.0, min(1.0, float(payload.get("score", 0.0))))
        stored["icp_score_reason"] = payload.get("explanation")
        stored["fit_signals"] = list(payload.get("fit_signals", []))
        stored["gap_signals"] = list(payload.get("gap_signals", []))
        stored["updated_at"] = utc_now()
        self.state.publish_event("lead_scored", {"lead_id": lead_id, "org_id": org_id, "score": stored["icp_score"]})
        return LeadResponse.model_validate(stored)

