from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_org_id
from backend.api.schemas.analytics import AnalyticsOverview, OutboundMetrics, PipelineMetrics, RetentionMetrics
from backend.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/pipeline", response_model=PipelineMetrics)
async def pipeline_metrics(org_id: str = Depends(get_org_id)) -> PipelineMetrics:
    overview = await analytics_service.get_overview(org_id)
    return overview.pipeline


@router.get("/outbound", response_model=OutboundMetrics)
async def outbound_metrics(org_id: str = Depends(get_org_id)) -> OutboundMetrics:
    overview = await analytics_service.get_overview(org_id)
    return overview.outbound


@router.get("/retention", response_model=RetentionMetrics)
async def retention_metrics(org_id: str = Depends(get_org_id)) -> RetentionMetrics:
    overview = await analytics_service.get_overview(org_id)
    return overview.retention


@router.get("/usage", response_model=AnalyticsOverview)
async def usage_metrics(org_id: str = Depends(get_org_id)) -> AnalyticsOverview:
    return await analytics_service.get_overview(org_id)

