from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from backend.api.schemas.campaigns import CampaignCreate, CampaignResponse, SequenceResponse
from backend.api.schemas.leads import LeadResponse
from backend.core.context_builder import ContextBuilder, build_context_builder
from backend.core.exceptions import NotFoundError
from backend.core.llm_router import LLMRouter, build_llm_router
from backend.core.prompt_manager import PromptManager, build_prompt_manager

from .base import BaseService
from .state import generate_id, utc_now


@dataclass(slots=True)
class CampaignService(BaseService):
    llm_router: LLMRouter = field(default_factory=build_llm_router)
    context_builder: ContextBuilder = field(default_factory=build_context_builder)
    prompt_manager: PromptManager = field(default_factory=build_prompt_manager)

    async def create_campaign(self, org_id: str, data: CampaignCreate) -> CampaignResponse:
        campaign_id = generate_id("campaign")
        now = utc_now()
        record = {
            "id": campaign_id,
            "org_id": org_id,
            "active": True,
            "sequences": [],
            "created_at": now,
            "updated_at": now,
            **data.model_dump(),
        }
        self.state.campaigns[campaign_id] = record
        return CampaignResponse.model_validate(record)

    async def list_campaigns(self, org_id: str) -> list[CampaignResponse]:
        return [
            CampaignResponse.model_validate(campaign)
            for campaign in self.state.campaigns.values()
            if campaign["org_id"] == org_id
        ]

    async def get_campaign(self, org_id: str, campaign_id: str) -> CampaignResponse:
        campaign = self.state.campaigns.get(campaign_id)
        if not campaign or campaign["org_id"] != org_id:
            raise NotFoundError("Campaign not found")
        return CampaignResponse.model_validate(campaign)

    async def generate_outbound(self, org_id: str, campaign_id: str, lead: LeadResponse) -> list[SequenceResponse]:
        campaign = await self.get_campaign(org_id, campaign_id)
        context = self.context_builder.build_full_outbound_context(
            contact=lead.model_dump(),
            campaign=campaign.model_dump(),
            enrichment=lead.enrichment_data,
        )
        response = await self.llm_router.complete(
            system=self.prompt_manager.load("outbound_personalization"),
            user=context,
            format="json",
            metadata={"org_id": org_id, "agent_name": "outbound_agent"},
        )
        payload = json.loads(response.content)
        variations: list[dict[str, Any]] = payload.get("variations", [])
        if not variations:
            variations = [
                {
                    "subject": "Quick question",
                    "body": "Would you be open to a short chat?",
                    "hook_type": "direct",
                    "confidence": 0.7,
                }
            ]
        sequences: list[SequenceResponse] = []
        for rank, variation in enumerate(variations[:3], start=1):
            sequence = {
                "id": generate_id("sequence"),
                "campaign_id": campaign_id,
                "lead_id": lead.id,
                "variation_rank": rank,
                "subject": variation.get("subject", f"Variation {rank}"),
                "body": variation.get("body", ""),
                "hook_type": variation.get("hook_type"),
                "confidence": float(variation.get("confidence", 0.0)),
                "status": "pending_approval",
                "created_at": utc_now(),
            }
            self.state.approvals[sequence["id"]] = {
                "id": sequence["id"],
                "org_id": org_id,
                "target_type": "sequence",
                "target_id": sequence["id"],
                "title": sequence["subject"],
                "body": sequence["body"],
                "status": "pending",
                "reviewer_id": None,
                "reviewed_at": None,
                "metadata": {"campaign_id": campaign_id, "lead_id": lead.id},
                "created_at": sequence["created_at"],
                "updated_at": sequence["created_at"],
            }
            campaign_sequences = self.state.campaigns[campaign_id].setdefault("sequences", [])
            campaign_sequences.append(sequence)
            sequences.append(SequenceResponse.model_validate(sequence))
        self.state.publish_event("outbound_generated", {"org_id": org_id, "campaign_id": campaign_id, "lead_id": lead.id})
        return sequences

