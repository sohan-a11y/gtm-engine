from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, File, Form, UploadFile

from backend.api.dependencies import get_org_id
from backend.api.schemas.common import PaginationParams
from backend.api.schemas.leads import LeadCreate, LeadImportResult, LeadListResponse, LeadResponse, LeadUpdate
from backend.core.exceptions import ValidationError
from backend.services import lead_service

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=LeadListResponse)
async def list_leads(org_id: str = Depends(get_org_id), pagination: PaginationParams = Depends()) -> LeadListResponse:
    leads = await lead_service.list_leads(org_id)
    start = (pagination.page - 1) * pagination.page_size
    items = leads[start : start + pagination.page_size]
    return LeadListResponse(items=items, total=len(leads), page=pagination.page, page_size=pagination.page_size)


@router.post("", response_model=LeadResponse)
async def create_lead(request: LeadCreate, org_id: str = Depends(get_org_id)) -> LeadResponse:
    return await lead_service.create_lead(org_id, request)


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: str, org_id: str = Depends(get_org_id)) -> LeadResponse:
    return await lead_service.get_lead(org_id, lead_id)


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: str, request: LeadUpdate, org_id: str = Depends(get_org_id)) -> LeadResponse:
    return await lead_service.update_lead(org_id, lead_id, request)


@router.post("/{lead_id}/score", response_model=LeadResponse)
async def score_lead(lead_id: str, org_id: str = Depends(get_org_id)) -> LeadResponse:
    return await lead_service.score_lead(org_id, lead_id)


@router.post("/import", response_model=LeadImportResult)
async def import_leads(
    org_id: str = Depends(get_org_id),
    upload: UploadFile | None = File(default=None),
    rows: str | None = Form(default=None),
) -> LeadImportResult:
    parsed: list[LeadCreate] = []
    if upload is not None:
        content = (await upload.read()).decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            parsed.append(LeadCreate.model_validate(row))
    elif rows:
        parsed.append(LeadCreate.model_validate_json(rows))
    else:
        raise ValidationError("Provide a CSV upload or JSON rows payload")
    return await lead_service.import_leads(org_id, parsed)

