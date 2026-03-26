from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_current_user, get_org_id, get_orchestrator
from backend.api.schemas.agents import AgentActionRequest, AgentActionResponse
from backend.api.schemas.auth import UserResponse
from backend.core.exceptions import ValidationError
from backend.services import campaign_service, deal_service, lead_service

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/{agent_type}/score", response_model=AgentActionResponse)
async def score_agent(
    agent_type: str,
    request: AgentActionRequest,
    org_id: str = Depends(get_org_id),
    _current_user: UserResponse = Depends(get_current_user),
) -> AgentActionResponse:
    if agent_type == "icp":
        lead_id = request.payload.get("lead_id")
        if not lead_id:
            raise ValidationError("lead_id is required")
        result = await lead_service.score_lead(org_id, lead_id)
        return AgentActionResponse(agent_name="icp_agent", status="completed", result=result.model_dump())
    if agent_type == "deal_intel":
        deal_id = request.payload.get("deal_id")
        if not deal_id:
            raise ValidationError("deal_id is required")
        result = await deal_service.analyze_risk(org_id, deal_id)
        return AgentActionResponse(agent_name="deal_intel_agent", status="completed", result=result.model_dump())
    workflow = await get_orchestrator().run_workflow(agent_type, {"org_id": org_id, **request.payload})
    return AgentActionResponse(agent_name=agent_type, status=workflow.status, result={"steps": workflow.steps})


@router.post("/{agent_type}/generate", response_model=AgentActionResponse)
async def generate_agent(
    agent_type: str,
    request: AgentActionRequest,
    org_id: str = Depends(get_org_id),
    _current_user: UserResponse = Depends(get_current_user),
) -> AgentActionResponse:
    if agent_type == "outbound":
        lead_id = request.payload.get("lead_id")
        campaign_id = request.payload.get("campaign_id")
        if not lead_id or not campaign_id:
            raise ValidationError("lead_id and campaign_id are required")
        lead = await lead_service.get_lead(org_id, lead_id)
        result = await campaign_service.generate_outbound(org_id, campaign_id, lead)
        return AgentActionResponse(
            agent_name="outbound_agent",
            status="completed",
            result={"sequences": [item.model_dump() for item in result]},
        )
    workflow = await get_orchestrator().run_workflow(agent_type, {"org_id": org_id, **request.payload})
    return AgentActionResponse(agent_name=agent_type, status=workflow.status, result={"steps": workflow.steps})


@router.post("/{agent_type}/analyze", response_model=AgentActionResponse)
async def analyze_agent(
    agent_type: str,
    request: AgentActionRequest,
    org_id: str = Depends(get_org_id),
    _current_user: UserResponse = Depends(get_current_user),
) -> AgentActionResponse:
    workflow = await get_orchestrator().run_workflow(agent_type, {"org_id": org_id, **request.payload})
    return AgentActionResponse(agent_name=agent_type, status=workflow.status, result={"steps": workflow.steps})
