from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_org_id
from backend.api.schemas.common import PaginationParams
from backend.api.schemas.integrations import (
    IntegrationConnectRequest,
    IntegrationListResponse,
    IntegrationResponse,
    IntegrationSyncResult,
)
from backend.services import integration_service

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=IntegrationListResponse)
async def list_integrations(org_id: str = Depends(get_org_id), pagination: PaginationParams = Depends()) -> IntegrationListResponse:
    integrations = await integration_service.list_integrations(org_id)
    start = (pagination.page - 1) * pagination.page_size
    items = integrations[start : start + pagination.page_size]
    return IntegrationListResponse(items=items, total=len(integrations), page=pagination.page, page_size=pagination.page_size)


@router.post("", response_model=IntegrationResponse)
async def connect_integration(request: IntegrationConnectRequest, org_id: str = Depends(get_org_id)) -> IntegrationResponse:
    return await integration_service.connect(org_id, request)


@router.post("/{integration_id}/sync", response_model=IntegrationSyncResult)
async def sync_integration(integration_id: str, org_id: str = Depends(get_org_id)) -> IntegrationSyncResult:
    return await integration_service.sync(org_id, integration_id)


@router.delete("/{integration_id}", response_model=IntegrationResponse)
async def disconnect_integration(integration_id: str, org_id: str = Depends(get_org_id)) -> IntegrationResponse:
    return await integration_service.disconnect(org_id, integration_id)

