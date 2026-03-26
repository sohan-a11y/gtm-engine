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


TASK_REGISTRY = {
    "enrich_contact": enrich_contact,
    "score_icp": score_icp,
    "generate_outbound": generate_outbound,
    "sync_crm": sync_crm,
    "weekly_digest": weekly_digest,
}


def dispatch_task(task_name: str, **kwargs: Any) -> dict[str, Any]:
    task = TASK_REGISTRY.get(task_name)
    if not task:
        return {"task_name": task_name, "dispatched": False}
    async_result = task.apply_async(kwargs=kwargs)
    return {"task_name": task_name, "task_id": async_result.id, "dispatched": True}
