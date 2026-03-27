from __future__ import annotations

import asyncio
from typing import Any

from backend.core.logging_config import get_logger
from backend.services import campaign_service, lead_service
from backend.services.state import STATE, utc_now
from backend.workers.celery_app import celery_app

logger = get_logger("gtm.worker")


def _run_async(coro):
    return asyncio.run(coro)


def _mark_job(job_id: str, status: str, result: Any | None = None) -> None:
    job = STATE.jobs.get(job_id)
    if not job:
        return
    job["status"] = status
    job["updated_at"] = utc_now()
    if result is not None:
        job["result"] = result


@celery_app.task(name="backend.workers.tasks.enrich_contact")
def enrich_contact(
    contact_id: str,
    org_id: str,
    job_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    logger.info("enrich_contact", extra={"contact_id": contact_id, "org_id": org_id})
    if job_id:
        _mark_job(job_id, "running")
    result = {"contact_id": contact_id, "org_id": org_id, "enrichment_status": "skipped"}
    if job_id:
        _mark_job(job_id, "completed", result)
    return result


@celery_app.task(name="backend.workers.tasks.score_icp")
def score_icp(
    lead_id: str,
    org_id: str,
    job_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    logger.info("score_icp", extra={"lead_id": lead_id, "org_id": org_id})
    if job_id:
        _mark_job(job_id, "running")
    result = _run_async(lead_service.score_lead(org_id, lead_id)).model_dump()
    if job_id:
        _mark_job(job_id, "completed", result)
    return result


@celery_app.task(name="backend.workers.tasks.generate_outbound")
def generate_outbound(
    lead_id: str,
    campaign_id: str,
    org_id: str,
    job_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    logger.info("generate_outbound", extra={"lead_id": lead_id, "campaign_id": campaign_id, "org_id": org_id})
    if job_id:
        _mark_job(job_id, "running")
    lead = _run_async(lead_service.get_lead(org_id, lead_id))
    result = _run_async(campaign_service.generate_outbound(org_id, campaign_id, lead))
    payload = {"sequences": [item.model_dump() for item in result]}
    if job_id:
        _mark_job(job_id, "completed", payload)
    return payload


@celery_app.task(name="backend.workers.tasks.sync_crm")
def sync_crm(
    org_id: str,
    job_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    logger.info("sync_crm", extra={"org_id": org_id})
    if job_id:
        _mark_job(job_id, "running")
    result = {"org_id": org_id, "synced": 0}
    if job_id:
        _mark_job(job_id, "completed", result)
    return result


@celery_app.task(name="backend.workers.tasks.weekly_digest")
def weekly_digest(
    org_id: str,
    job_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    logger.info("weekly_digest", extra={"org_id": org_id})
    if job_id:
        _mark_job(job_id, "running")
    result = {"org_id": org_id, "summary": "digest generated"}
    if job_id:
        _mark_job(job_id, "completed", result)
    return result


@celery_app.task(name="backend.workers.tasks.send_approved_sequences")
def send_approved_sequences(
    org_id: str | None = None,
    job_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Dispatch all approved email sequences that have not yet been sent."""
    logger.info("send_approved_sequences", extra={"org_id": org_id or "all"})
    if job_id:
        _mark_job(job_id, "running")

    async def _run() -> dict[str, Any]:
        from sqlalchemy import select
        from backend.db.session import build_session_factory
        from backend.db.models import EmailSequence, Integration, Organization, Contact
        from backend.core.encryption import decrypt_payload
        from backend.integrations.email.gmail import GmailEmailClient
        from backend.integrations.email.outlook import OutlookEmailClient

        factory = build_session_factory()
        sent_count = 0
        error_count = 0

        async with factory() as session:
            # Get orgs to process
            if org_id:
                org_ids = [org_id]
            else:
                result = await session.execute(select(Organization.id).where(Organization.is_active.is_(True)))
                org_ids = [str(row[0]) for row in result.all()]

            for oid in org_ids:
                from uuid import UUID as _UUID
                try:
                    org_uuid = _UUID(oid)
                except Exception:
                    continue

                # Get email integration for this org
                int_result = await session.execute(
                    select(Integration).where(
                        Integration.org_id == org_uuid,
                        Integration.provider.in_(["gmail", "outlook"]),
                        Integration.status == "connected",
                    )
                )
                integration = int_result.scalar_one_or_none()
                if integration is None:
                    continue

                # Decrypt credentials
                try:
                    creds: dict = decrypt_payload(integration.credentials_encrypted or "")
                    email_token = creds.get("access_token", "") or creds.get("oauth_token", "")
                    from_address = creds.get("from_address", "") or creds.get("email", "")
                except Exception:
                    continue

                if not email_token:
                    continue

                # Pick email client
                if integration.provider == "gmail":
                    email_client = GmailEmailClient(oauth_token=email_token, from_address=from_address)
                else:
                    email_client = OutlookEmailClient(oauth_token=email_token, from_address=from_address)

                # Get approved sequences for this org
                seq_result = await session.execute(
                    select(EmailSequence).where(
                        EmailSequence.org_id == org_uuid,
                        EmailSequence.status == "approved",
                    ).limit(50)
                )
                sequences = seq_result.scalars().all()

                for seq in sequences:
                    try:
                        # Get contact email
                        if seq.contact_id is None:
                            continue
                        contact_result = await session.execute(
                            select(Contact).where(Contact.id == seq.contact_id)
                        )
                        contact = contact_result.scalar_one_or_none()
                        if contact is None or not contact.email:
                            continue

                        send_result = await email_client.send_email(
                            to=contact.email,
                            subject=seq.subject,
                            body=seq.body,
                        )
                        if send_result.get("status") in ("sent", "queued"):
                            from backend.db.models import utc_now as _now
                            seq.status = "sent"
                            seq.sent_at = _now()
                            sent_count += 1
                        else:
                            error_count += 1
                    except Exception as exc:
                        logger.error("send_approved_sequences: error sending seq %s: %s", seq.id, exc)
                        error_count += 1

            await session.commit()

        return {"sent": sent_count, "errors": error_count}

    task_result = _run_async(_run())
    if job_id:
        _mark_job(job_id, "completed", task_result)
    return task_result


@celery_app.task(name="backend.workers.tasks.batch_score")
def batch_score(
    org_id: str | None = None,
    job_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score all unscored contacts using the ICP agent."""
    logger.info("batch_score", extra={"org_id": org_id or "all"})
    if job_id:
        _mark_job(job_id, "running")

    async def _run() -> dict[str, Any]:
        from sqlalchemy import select
        from backend.db.session import build_session_factory
        from backend.db.models import Contact, Organization

        factory = build_session_factory()
        scored = 0

        async with factory() as session:
            if org_id:
                org_ids = [org_id]
            else:
                result = await session.execute(select(Organization.id).where(Organization.is_active.is_(True)))
                org_ids = [str(row[0]) for row in result.all()]

            for oid in org_ids:
                from uuid import UUID as _UUID
                try:
                    org_uuid = _UUID(oid)
                except Exception:
                    continue
                result = await session.execute(
                    select(Contact).where(
                        Contact.org_id == org_uuid,
                        Contact.icp_score.is_(None),
                        Contact.status.in_(["new", "enriched"]),
                    ).limit(20)
                )
                contacts = result.scalars().all()
                for contact in contacts:
                    try:
                        await lead_service.score_lead(oid, str(contact.id), session=session)
                        scored += 1
                    except Exception as exc:
                        logger.debug("batch_score: error scoring contact %s: %s", contact.id, exc)

        return {"scored": scored}

    task_result = _run_async(_run())
    if job_id:
        _mark_job(job_id, "completed", task_result)
    return task_result


TASK_REGISTRY = {
    "enrich_contact": enrich_contact,
    "score_icp": score_icp,
    "generate_outbound": generate_outbound,
    "sync_crm": sync_crm,
    "weekly_digest": weekly_digest,
    "send_approved_sequences": send_approved_sequences,
    "batch_score": batch_score,
}


def dispatch_task(task_name: str, **kwargs: Any) -> dict[str, Any]:
    task = TASK_REGISTRY.get(task_name)
    if not task:
        return {"task_name": task_name, "dispatched": False}
    async_result = task.apply_async(kwargs=kwargs)
    return {"task_name": task_name, "task_id": async_result.id, "dispatched": True}
