from __future__ import annotations

from dataclasses import dataclass

from backend.api.schemas.companies import CompanyCreate, CompanyResponse, CompanyUpdate
from backend.core.exceptions import NotFoundError

from .base import BaseService
from .state import generate_id, utc_now


@dataclass(slots=True)
class CompanyService(BaseService):
    async def create_company(self, org_id: str, data: CompanyCreate) -> CompanyResponse:
        company_id = generate_id("company")
        now = utc_now()
        record = {"id": company_id, "org_id": org_id, "created_at": now, "updated_at": now, **data.model_dump()}
        self.state.companies[company_id] = record
        return CompanyResponse.model_validate(record)

    async def list_companies(self, org_id: str) -> list[CompanyResponse]:
        return [
            CompanyResponse.model_validate(company)
            for company in self.state.companies.values()
            if company["org_id"] == org_id
        ]

    async def get_company(self, org_id: str, company_id: str) -> CompanyResponse:
        company = self.state.companies.get(company_id)
        if not company or company["org_id"] != org_id:
            raise NotFoundError("Company not found")
        return CompanyResponse.model_validate(company)

    async def update_company(self, org_id: str, company_id: str, data: CompanyUpdate) -> CompanyResponse:
        company = self.state.companies.get(company_id)
        if not company or company["org_id"] != org_id:
            raise NotFoundError("Company not found")
        company.update(data.model_dump(exclude_none=True))
        company["updated_at"] = utc_now()
        return CompanyResponse.model_validate(company)

