from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_org_id
from backend.core.exceptions import NotFoundError
from backend.services.state import STATE, generate_id, utc_now
from backend.workers.tasks import dispatch_task

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _create_job(org_id: str, job_type: str, payload: dict[str, object]) -> dict[str, object]:
    job_id = generate_id("job")
    record = {
        "id": job_id,
        "org_id": org_id,
        "type": job_type,
        "status": "queued",
        "payload": payload,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    STATE.jobs[job_id] = record
    dispatch_task(job_type, org_id=org_id, job_id=job_id, payload=payload)
    return record


@router.post("/run-weekly-digest")
async def run_weekly_digest(org_id: str = Depends(get_org_id)) -> dict[str, object]:
    return _create_job(org_id, "weekly_digest", {})


@router.post("/run-sync")
async def run_sync(org_id: str = Depends(get_org_id)) -> dict[str, object]:
    return _create_job(org_id, "sync_crm", {})


@router.post("/run-batch-score")
async def run_batch_score(org_id: str = Depends(get_org_id)) -> dict[str, object]:
    return _create_job(org_id, "batch_score", {})


@router.post("/run-crm-sync")
async def run_crm_sync_job(org_id: str = Depends(get_org_id)) -> dict[str, object]:
    return _create_job(org_id, "sync_crm", {})


@router.get("/{job_id}/status")
async def get_job_status(job_id: str, org_id: str = Depends(get_org_id)) -> dict[str, object]:
    job = STATE.jobs.get(job_id)
    if not job or job["org_id"] != org_id:
        raise NotFoundError("Job not found")
    return job

