from __future__ import annotations

import asyncio

from backend.agents.content_agent import ContentAgent
from backend.agents.deal_intel_agent import DealIntelAgent
from backend.agents.icp_agent import ICPAgent
from backend.agents.outbound_agent import OutboundAgent
from backend.agents.retention_agent import RetentionAgent


def test_icp_agent_fallback_and_training(llm_router):
    async def scenario():
        agent = ICPAgent(llm_router=llm_router)
        empty_result = await agent.score(org_id="org-1", contact_profile={"company": "Acme"})
        assert empty_result.requires_training is True
        train_result = await agent.train(
            org_id="org-1",
            profiles=[
                {"label": "good", "name": "Alice", "company": "Acme", "pain_points": "manual outreach"},
                {"label": "good", "name": "Bob", "company": "Acme", "pain_points": "pipeline"},
                {"label": "good", "name": "Cara", "company": "Acme", "pain_points": "workflow"},
            ],
        )
        assert train_result["status"] == "trained"
        scored = await agent.score(org_id="org-1", contact_profile={"company": "Acme", "pain_points": "pipeline"})
        assert scored.score is not None
        assert scored.training_profile_count == 3

    asyncio.run(scenario())


def test_outbound_agent_generates_three_variations(llm_router):
    async def scenario():
        agent = OutboundAgent(llm_router=llm_router)
        result = await agent.generate_variations(
            contact={"first_name": "Jane", "company_name": "Acme"},
            campaign={"name": "Q2 outbound", "value_prop": "reduce manual work"},
        )
        assert len(result.variations) == 3
        assert all(variation.subject for variation in result.variations)

    asyncio.run(scenario())


def test_content_agent_flags_weak_cta(llm_router):
    async def scenario():
        agent = ContentAgent(llm_router=llm_router)
        draft = await agent.generate_linkedin_post(topic="AI GTM engine", brand_voice="clear and concise")
        assert draft.mode == "LINKEDIN_POST"
        assert isinstance(draft.quality_flags, list)

    asyncio.run(scenario())


def test_deal_and_retention_agents_return_structured_results(llm_router):
    async def scenario():
        deal_agent = DealIntelAgent(llm_router=llm_router)
        retention_agent = RetentionAgent(llm_router=llm_router)
        deal_result = await deal_agent.analyze(deal={"name": "Deal", "days_in_stage": 12, "amount_cents": 500000})
        retention_result = await retention_agent.analyze(account={"dau_mau": 0.55, "open_tickets": 2})
        assert 0.0 <= deal_result.risk_score <= 1.0
        assert retention_result.health_state in {"Thriving", "Stable", "At Risk", "In Danger", "Critical"}

    asyncio.run(scenario())
