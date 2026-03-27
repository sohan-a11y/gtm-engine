from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db_session, get_org_id
from backend.api.schemas.common import PaginationParams
from backend.api.schemas.deals import DealCreate, DealListResponse, DealResponse, DealUpdate
from backend.services import deal_service

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("", response_model=DealListResponse)
async def list_deals(
    org_id: str = Depends(get_org_id),
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> DealListResponse:
    deals = await deal_service.list_deals(org_id, session=session)
    start = (pagination.page - 1) * pagination.page_size
    items = deals[start : start + pagination.page_size]
    return DealListResponse(items=items, total=len(deals), page=pagination.page, page_size=pagination.page_size)


@router.post("", response_model=DealResponse)
async def create_deal(
    request: DealCreate,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> DealResponse:
    return await deal_service.create_deal(org_id, request, session=session)


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: str,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> DealResponse:
    return await deal_service.get_deal(org_id, deal_id, session=session)


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: str,
    request: DealUpdate,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> DealResponse:
    return await deal_service.update_deal(org_id, deal_id, request, session=session)


@router.post("/{deal_id}/risk", response_model=DealResponse)
async def analyze_risk(
    deal_id: str,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> DealResponse:
    return await deal_service.analyze_risk(org_id, deal_id, session=session)
