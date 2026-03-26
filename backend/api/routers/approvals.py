from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_current_user, get_org_id
from backend.api.schemas.approvals import ApprovalActionRequest, ApprovalItem, ApprovalListResponse
from backend.api.schemas.auth import UserResponse
from backend.api.schemas.common import PaginationParams
from backend.services import approval_service

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=ApprovalListResponse)
async def list_approvals(org_id: str = Depends(get_org_id), pagination: PaginationParams = Depends()) -> ApprovalListResponse:
    approvals = await approval_service.list_approvals(org_id)
    start = (pagination.page - 1) * pagination.page_size
    items = approvals[start : start + pagination.page_size]
    return ApprovalListResponse(items=items, total=len(approvals), page=pagination.page, page_size=pagination.page_size)


@router.post("/{approval_id}/approve", response_model=ApprovalItem)
async def approve(
    approval_id: str,
    request: ApprovalActionRequest,
    org_id: str = Depends(get_org_id),
    current_user: UserResponse = Depends(get_current_user),
) -> ApprovalItem:
    return await approval_service.approve(org_id, approval_id, current_user.id, request)


@router.post("/{approval_id}/reject", response_model=ApprovalItem)
async def reject(
    approval_id: str,
    request: ApprovalActionRequest,
    org_id: str = Depends(get_org_id),
    current_user: UserResponse = Depends(get_current_user),
) -> ApprovalItem:
    return await approval_service.reject(org_id, approval_id, current_user.id, request)

