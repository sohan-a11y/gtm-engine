from __future__ import annotations

from dataclasses import dataclass

from backend.api.schemas.approvals import ApprovalActionRequest, ApprovalItem
from backend.core.exceptions import NotFoundError

from .base import BaseService
from .state import utc_now


@dataclass(slots=True)
class ApprovalService(BaseService):
    async def list_approvals(self, org_id: str) -> list[ApprovalItem]:
        return [
            ApprovalItem.model_validate(item)
            for item in self.state.approvals.values()
            if item["org_id"] == org_id
        ]

    async def get_approval(self, org_id: str, approval_id: str) -> ApprovalItem:
        item = self.state.approvals.get(approval_id)
        if not item or item["org_id"] != org_id:
            raise NotFoundError("Approval not found")
        return ApprovalItem.model_validate(item)

    async def approve(self, org_id: str, approval_id: str, reviewer_id: str, request: ApprovalActionRequest) -> ApprovalItem:
        item = self.state.approvals.get(approval_id)
        if not item or item["org_id"] != org_id:
            raise NotFoundError("Approval not found")
        item["status"] = "approved"
        item["reviewer_id"] = reviewer_id
        item["reviewed_at"] = utc_now()
        item["updated_at"] = utc_now()
        item["metadata"]["note"] = request.note
        return ApprovalItem.model_validate(item)

    async def reject(self, org_id: str, approval_id: str, reviewer_id: str, request: ApprovalActionRequest) -> ApprovalItem:
        item = self.state.approvals.get(approval_id)
        if not item or item["org_id"] != org_id:
            raise NotFoundError("Approval not found")
        item["status"] = "rejected"
        item["reviewer_id"] = reviewer_id
        item["reviewed_at"] = utc_now()
        item["updated_at"] = utc_now()
        item["metadata"]["note"] = request.note
        return ApprovalItem.model_validate(item)

