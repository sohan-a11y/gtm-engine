from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.dependencies import get_db_session, get_org_id
from backend.db.models import AgentAuditLog
from uuid import UUID

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("")
async def list_notifications(
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
    limit: int = 30,
) -> list[dict]:
    result = await session.execute(
        select(AgentAuditLog)
        .where(AgentAuditLog.org_id == UUID(org_id))
        .order_by(desc(AgentAuditLog.created_at))
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "event_type": r.operation,
            "agent_name": r.agent_name,
            "message": _summarize(r),
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "metadata": r.metadata_json or {},
        }
        for r in rows
    ]

def _summarize(r: AgentAuditLog) -> str:
    meta = r.metadata_json or {}
    if r.operation == "lead_scored":
        score = meta.get("score", "")
        return f"Lead scored: {score}"
    if r.operation == "outbound_draft_ready":
        return "New outbound draft ready for review"
    if r.operation == "sync_complete":
        return f"CRM sync complete: {meta.get('provider', 'unknown')}"
    if r.operation == "deal_risk_analyzed":
        risk = meta.get("risk_level", "")
        return f"Deal risk analyzed: {risk}"
    return r.operation.replace("_", " ").title()
