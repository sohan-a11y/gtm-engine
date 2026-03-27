from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db_session, get_org_id
from backend.api.schemas.campaigns import CampaignCreate, CampaignListResponse, CampaignResponse, CampaignUpdate, SequenceResponse
from backend.api.schemas.common import PaginationParams
from backend.services import campaign_service, lead_service

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    org_id: str = Depends(get_org_id),
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> CampaignListResponse:
    campaigns = await campaign_service.list_campaigns(org_id, session=session)
    start = (pagination.page - 1) * pagination.page_size
    items = campaigns[start : start + pagination.page_size]
    return CampaignListResponse(items=items, total=len(campaigns), page=pagination.page, page_size=pagination.page_size)


@router.post("", response_model=CampaignResponse)
async def create_campaign(
    request: CampaignCreate,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> CampaignResponse:
    return await campaign_service.create_campaign(org_id, request, session=session)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> CampaignResponse:
    return await campaign_service.get_campaign(org_id, campaign_id, session=session)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    request: CampaignUpdate,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> CampaignResponse:
    return await campaign_service.update_campaign(org_id, campaign_id, request, session=session)


@router.get("/{campaign_id}/sequences", response_model=list[SequenceResponse])
async def list_sequences(
    campaign_id: str,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> list[SequenceResponse]:
    campaign = await campaign_service.get_campaign(org_id, campaign_id, session=session)
    return list(campaign.sequences)


@router.post("/{campaign_id}/generate/{lead_id}", response_model=list[SequenceResponse])
async def generate_outbound(
    campaign_id: str,
    lead_id: str,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> list[SequenceResponse]:
    lead = await lead_service.get_lead(org_id, lead_id, session=session)
    return await campaign_service.generate_outbound(org_id, campaign_id, lead, session=session)
