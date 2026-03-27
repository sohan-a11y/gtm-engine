from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db_session, get_llm_router, get_org_id
from backend.api.schemas.common import PaginationParams
from backend.core.exceptions import AuthenticationError, NotFoundError, ServiceUnavailableError
from backend.core.llm_router import LLMRouter
from backend.db.models import AgentAuditLog
from backend.enrichment.transcript_parser import TranscriptInsight, TranscriptParser
from backend.services import deal_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


# ---------------------------------------------------------------------------
# Zoom webhook signature verification
# ---------------------------------------------------------------------------


def _verify_zoom_signature(body: bytes, signature: Optional[str]) -> None:
    secret = os.getenv("ZOOM_WEBHOOK_SECRET")
    if not secret:
        return
    if not signature:
        raise AuthenticationError("Missing x-zm-signature header")
    expected = "v0=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise AuthenticationError("Invalid Zoom webhook signature")


# ---------------------------------------------------------------------------
# Repository helper — store insight in agent_audit_log
# ---------------------------------------------------------------------------


async def _store_insight(
    *,
    org_id: str,
    insight: TranscriptInsight,
    deal_id: Optional[str],
    source: str,
    session: AsyncSession,
) -> AgentAuditLog:
    metadata: dict[str, Any] = {
        "summary": insight.summary,
        "action_items": insight.action_items,
        "competitor_mentions": insight.competitor_mentions,
        "buying_signals": insight.buying_signals,
        "objections": insight.objections,
        "sentiment": insight.sentiment,
        "engagement_score": insight.engagement_score,
        "parser_metadata": insight.metadata,
        "source": source,
    }
    if deal_id:
        metadata["deal_id"] = deal_id

    record = AgentAuditLog(
        org_id=UUID(org_id),
        agent_name="transcript_parser",
        operation="transcript_ingested",
        metadata_json=metadata,
        success=True,
    )
    session.add(record)
    await session.flush()
    await session.commit()
    return record


# ---------------------------------------------------------------------------
# Response serialiser
# ---------------------------------------------------------------------------


def _insight_to_dict(insight: TranscriptInsight, record_id: Optional[str] = None) -> dict[str, Any]:
    return {
        "id": record_id,
        "summary": insight.summary,
        "action_items": insight.action_items,
        "competitor_mentions": insight.competitor_mentions,
        "buying_signals": insight.buying_signals,
        "objections": insight.objections,
        "sentiment": insight.sentiment,
        "engagement_score": insight.engagement_score,
        "metadata": insight.metadata,
    }


# ---------------------------------------------------------------------------
# Ingest helper (shared by all upload paths)
# ---------------------------------------------------------------------------


async def _ingest(
    *,
    text: str,
    source: str,
    deal_id: Optional[str],
    org_id: str,
    llm_router: LLMRouter,
    session: AsyncSession,
) -> dict[str, Any]:
    parser = TranscriptParser(llm_router=llm_router)
    insight = parser.parse(text)

    record = await _store_insight(
        org_id=org_id,
        insight=insight,
        deal_id=deal_id,
        source=source,
        session=session,
    )

    if deal_id:
        try:
            await deal_service.attach_transcript(deal_id, insight, session=session)
        except Exception:
            logger.exception("attach_transcript failed for deal_id=%s; continuing", deal_id)

    return _insight_to_dict(insight, record_id=str(record.id))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/upload")
async def upload_transcript(
    request: Request,
    deal_id: Optional[str] = Query(default=None),
    file: Optional[UploadFile] = File(default=None),
    org_id: str = Depends(get_org_id),
    llm_router: LLMRouter = Depends(get_llm_router),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Upload a transcript as a .txt file (multipart) or raw text body."""
    if file is not None:
        raw_bytes = await file.read()
        text = raw_bytes.decode("utf-8", errors="replace")
    else:
        body = await request.body()
        content_type = request.headers.get("content-type", "")
        if "json" in content_type:
            payload = json.loads(body)
            text = payload.get("text", "") if isinstance(payload, dict) else body.decode("utf-8", errors="replace")
        else:
            text = body.decode("utf-8", errors="replace")

    if not text.strip():
        raise ServiceUnavailableError("No transcript text provided")

    return await _ingest(
        text=text,
        source="upload",
        deal_id=deal_id,
        org_id=org_id,
        llm_router=llm_router,
        session=session,
    )


@router.post("/zoom/webhook")
async def zoom_webhook(
    request: Request,
    x_zm_signature: Optional[str] = Header(default=None),
    deal_id: Optional[str] = Query(default=None),
    org_id: str = Depends(get_org_id),
    llm_router: LLMRouter = Depends(get_llm_router),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Receive a Zoom webhook with a meeting transcript."""
    body = await request.body()
    _verify_zoom_signature(body, x_zm_signature)

    try:
        payload: dict[str, Any] = json.loads(body)
    except Exception:
        raise ServiceUnavailableError("Invalid JSON in Zoom webhook body")

    # Zoom sends the VTT transcript under payload.object.transcript
    vtt_text: str = ""
    try:
        vtt_text = payload.get("payload", {}).get("object", {}).get("transcript", "")
    except Exception:
        pass

    if not vtt_text:
        # Fallback: try top-level "transcript" key
        vtt_text = str(payload.get("transcript", ""))

    text = TranscriptParser.from_zoom_vtt(vtt_text) if vtt_text.strip().startswith("WEBVTT") else vtt_text

    if not text.strip():
        return {"status": "accepted", "detail": "No transcript content found"}

    result = await _ingest(
        text=text,
        source="zoom_webhook",
        deal_id=deal_id,
        org_id=org_id,
        llm_router=llm_router,
        session=session,
    )
    return {"status": "accepted", **result}


@router.post("/gong/webhook")
async def gong_webhook(
    request: Request,
    deal_id: Optional[str] = Query(default=None),
    org_id: str = Depends(get_org_id),
    llm_router: LLMRouter = Depends(get_llm_router),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Receive a Gong webhook with a call transcript."""
    body = await request.body()

    try:
        payload: dict[str, Any] = json.loads(body)
    except Exception:
        raise ServiceUnavailableError("Invalid JSON in Gong webhook body")

    text = TranscriptParser.from_gong_json(payload)

    if not text.strip():
        return {"status": "accepted", "detail": "No transcript content found"}

    result = await _ingest(
        text=text,
        source="gong_webhook",
        deal_id=deal_id,
        org_id=org_id,
        llm_router=llm_router,
        session=session,
    )
    return {"status": "accepted", **result}


@router.get("")
async def list_transcripts(
    pagination: PaginationParams = Depends(),
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """List ingested transcripts for the org, newest first."""
    from sqlalchemy import desc, select

    stmt = (
        select(AgentAuditLog)
        .where(
            AgentAuditLog.org_id == UUID(org_id),
            AgentAuditLog.operation == "transcript_ingested",
        )
        .order_by(desc(AgentAuditLog.created_at))
        .limit(pagination.page_size)
        .offset((pagination.page - 1) * pagination.page_size)
    )
    from sqlalchemy import func, select as sel2

    count_stmt = sel2(func.count()).select_from(AgentAuditLog).where(
        AgentAuditLog.org_id == UUID(org_id),
        AgentAuditLog.operation == "transcript_ingested",
    )
    result = await session.execute(stmt)
    count_result = await session.execute(count_stmt)
    records = result.scalars().all()
    total: int = count_result.scalar_one_or_none() or 0

    items = []
    for rec in records:
        meta = rec.metadata_json or {}
        items.append(
            {
                "id": str(rec.id),
                "created_at": rec.created_at.isoformat(),
                "deal_id": meta.get("deal_id"),
                "source": meta.get("source"),
                "summary": meta.get("summary", ""),
                "sentiment": meta.get("sentiment", "neutral"),
                "engagement_score": meta.get("engagement_score", 0.0),
            }
        )

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
    }


@router.get("/{transcript_id}")
async def get_transcript(
    transcript_id: str,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Get a single transcript with full parsed insights."""
    from sqlalchemy import select

    stmt = select(AgentAuditLog).where(
        AgentAuditLog.org_id == UUID(org_id),
        AgentAuditLog.id == UUID(transcript_id),
        AgentAuditLog.operation == "transcript_ingested",
    )
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        raise NotFoundError("Transcript not found")

    meta = record.metadata_json or {}
    return {
        "id": str(record.id),
        "created_at": record.created_at.isoformat(),
        "deal_id": meta.get("deal_id"),
        "source": meta.get("source"),
        "summary": meta.get("summary", ""),
        "action_items": meta.get("action_items", []),
        "competitor_mentions": meta.get("competitor_mentions", []),
        "buying_signals": meta.get("buying_signals", []),
        "objections": meta.get("objections", []),
        "sentiment": meta.get("sentiment", "neutral"),
        "engagement_score": meta.get("engagement_score", 0.0),
        "metadata": meta.get("parser_metadata", {}),
    }
