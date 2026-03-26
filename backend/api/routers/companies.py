from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_org_id
from backend.api.schemas.companies import CompanyCreate, CompanyListResponse, CompanyResponse, CompanyUpdate
from backend.api.schemas.common import PaginationParams
from backend.services import company_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
async def list_companies(org_id: str = Depends(get_org_id), pagination: PaginationParams = Depends()) -> CompanyListResponse:
    companies = await company_service.list_companies(org_id)
    start = (pagination.page - 1) * pagination.page_size
    items = companies[start : start + pagination.page_size]
    return CompanyListResponse(items=items, total=len(companies), page=pagination.page, page_size=pagination.page_size)


@router.post("", response_model=CompanyResponse)
async def create_company(request: CompanyCreate, org_id: str = Depends(get_org_id)) -> CompanyResponse:
    return await company_service.create_company(org_id, request)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str, org_id: str = Depends(get_org_id)) -> CompanyResponse:
    return await company_service.get_company(org_id, company_id)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: str, request: CompanyUpdate, org_id: str = Depends(get_org_id)) -> CompanyResponse:
    return await company_service.update_company(org_id, company_id, request)

