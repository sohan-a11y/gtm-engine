from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db_session
from backend.core.encryption import decrypt_payload
from backend.core.exceptions import AuthenticationError
from backend.db.models import Integration
from backend.db.repositories.company_repo import CompanyRepository
from backend.db.repositories.contact_repo import ContactRepository
from backend.db.repositories.deal_repo import DealRepository
from backend.db.repositories.integration_repo import IntegrationRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------

def _verify_signature(body: bytes, signature: str | None) -> None:
    secret = os.getenv("WEBHOOK_SECRET")
    if not secret:
        return
    if not signature:
        raise AuthenticationError("Missing webhook signature")
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise AuthenticationError("Invalid webhook signature")


# ---------------------------------------------------------------------------
# HubSpot helpers
# ---------------------------------------------------------------------------

_HUBSPOT_OBJECT_TYPE_MAP: dict[str, str] = {
    "contact": "contacts",
    "deal": "deals",
    "company": "companies",
}


async def _fetch_hubspot_object(
    object_type: str, object_id: int | str, access_token: str
) -> dict[str, Any] | None:
    url = f"https://api.hubapi.com/crm/v3/objects/{object_type}/{object_id}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                params={"properties": "email,firstname,lastname,name,domain,amount,dealstage,industry,numberofemployees"},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("HubSpot fetch failed for %s/%s: %s", object_type, object_id, exc)
        return None


async def _upsert_hubspot_contact(
    org_id_str: str,
    object_id: int | str,
    props: dict[str, Any],
    session: AsyncSession,
) -> None:
    from uuid import UUID

    org_id = UUID(org_id_str)
    repo = ContactRepository(session)
    email = props.get("email") or ""
    if not email:
        return
    existing = await repo.get_by_email(org_id=org_id, email=email.lower())
    data: dict[str, Any] = {
        "email": email.lower(),
        "first_name": props.get("firstname") or "",
        "last_name": props.get("lastname") or "",
        "external_crm_id": str(object_id),
        "enrichment_data": props,
    }
    if existing is None:
        await repo.create(org_id=org_id, data=data)
    else:
        for k, v in data.items():
            if hasattr(existing, k):
                setattr(existing, k, v)
        await session.flush()


async def _upsert_hubspot_deal(
    org_id_str: str,
    object_id: int | str,
    props: dict[str, Any],
    session: AsyncSession,
) -> None:
    from uuid import UUID

    org_id = UUID(org_id_str)
    repo = DealRepository(session)
    name = props.get("dealname") or f"Deal {object_id}"
    stage = props.get("dealstage") or "prospecting"
    amount_raw = props.get("amount") or 0
    try:
        amount_cents = int(float(str(amount_raw)) * 100)
    except (TypeError, ValueError):
        amount_cents = 0

    # Look for existing deal by external_crm_id
    from sqlalchemy import select as _select
    from backend.db.models import Deal

    result = await session.execute(
        _select(Deal).where(Deal.org_id == org_id, Deal.external_crm_id == str(object_id))
    )
    existing = result.scalar_one_or_none()
    data: dict[str, Any] = {
        "name": name,
        "stage": stage,
        "amount_cents": amount_cents,
        "external_crm_id": str(object_id),
    }
    if existing is None:
        await repo.create(org_id=org_id, data=data)
    else:
        for k, v in data.items():
            if hasattr(existing, k):
                setattr(existing, k, v)
        await session.flush()


async def _upsert_hubspot_company(
    org_id_str: str,
    object_id: int | str,
    props: dict[str, Any],
    session: AsyncSession,
) -> None:
    from uuid import UUID

    org_id = UUID(org_id_str)
    repo = CompanyRepository(session)
    domain = props.get("domain") or None
    name = props.get("name") or f"Company {object_id}"

    existing = None
    if domain:
        existing = await repo.get_by_domain(org_id=org_id, domain=domain)
    if existing is None:
        from backend.db.models import Company
        result = await session.execute(
            select(Company).where(
                Company.org_id == org_id, Company.external_crm_id == str(object_id)
            )
        )
        existing = result.scalar_one_or_none()

    try:
        employee_count = int(props.get("numberofemployees") or 0) or None
    except (TypeError, ValueError):
        employee_count = None

    data: dict[str, Any] = {
        "name": name,
        "domain": domain,
        "industry": props.get("industry") or None,
        "employee_count": employee_count,
        "external_crm_id": str(object_id),
        "enrichment_data": props,
    }
    if existing is None:
        await repo.create(org_id=org_id, data=data)
    else:
        for k, v in data.items():
            if hasattr(existing, k):
                setattr(existing, k, v)
        await session.flush()


async def _resolve_org_by_portal(portal_id: int | str, session: AsyncSession) -> str | None:
    """Find org_id by matching portal_id stored in integration metadata_json."""
    result = await session.execute(
        select(Integration).where(Integration.provider == "hubspot")
    )
    integrations = result.scalars().all()
    portal_str = str(portal_id)
    for integ in integrations:
        meta = integ.metadata_json or {}
        if str(meta.get("portal_id", "")) == portal_str:
            return str(integ.org_id)
    return None


# ---------------------------------------------------------------------------
# Salesforce helpers
# ---------------------------------------------------------------------------

async def _fetch_salesforce_object(
    instance_url: str,
    access_token: str,
    sobject_type: str,
    object_id: str,
) -> dict[str, Any] | None:
    url = f"{instance_url.rstrip('/')}/services/data/v57.0/sobjects/{sobject_type}/{object_id}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Salesforce fetch failed for %s/%s: %s", sobject_type, object_id, exc)
        return None


async def _resolve_org_by_instance(instance_url: str, session: AsyncSession) -> str | None:
    """Find org_id by matching instance_url in integration metadata_json."""
    result = await session.execute(
        select(Integration).where(Integration.provider == "salesforce")
    )
    integrations = result.scalars().all()
    for integ in integrations:
        meta = integ.metadata_json or {}
        if meta.get("instance_url", "").rstrip("/") == instance_url.rstrip("/"):
            return str(integ.org_id)
    return None


# ---------------------------------------------------------------------------
# Gmail / Outlook reply helpers
# ---------------------------------------------------------------------------

async def _mark_replied_by_external_ref(
    ref_value: str,
    ref_field: str,
    session: AsyncSession,
) -> bool:
    """Find an EmailSequence by a metadata key and mark it replied."""
    from backend.db.models import EmailSequence, utc_now

    result = await session.execute(select(EmailSequence))
    sequences = result.scalars().all()
    for seq in sequences:
        meta = seq.metadata_json or {}
        if str(meta.get(ref_field, "")) == ref_value:
            seq.status = "replied"
            seq.metadata_json = {**meta, "replied_at": utc_now().isoformat()}
            await session.flush()
            await session.commit()
            return True
    return False


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/hubspot")
async def hubspot_webhook(
    request: Request,
    x_hubspot_signature: str | None = Header(default=None),
    org_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    body = await request.body()
    _verify_signature(body, x_hubspot_signature)

    try:
        import json

        events: list[dict[str, Any]] = json.loads(body)
    except Exception:
        logger.warning("HubSpot webhook: could not parse body")
        return {"status": "accepted"}

    for event in events:
        try:
            subscription_type: str = event.get("subscriptionType", "")
            object_id = event.get("objectId")
            portal_id = event.get("portalId")

            # Resolve org
            resolved_org_id = org_id
            if resolved_org_id is None and portal_id is not None:
                resolved_org_id = await _resolve_org_by_portal(portal_id, session)
            if resolved_org_id is None:
                logger.warning("HubSpot webhook: cannot resolve org for portalId=%s", portal_id)
                continue

            # Resolve integration credentials
            from uuid import UUID

            integ_repo = IntegrationRepository(session)
            integ = await integ_repo.get_by_provider(
                org_id=UUID(resolved_org_id), provider="hubspot"
            )
            if integ is None or not integ.credentials_encrypted:
                logger.warning("HubSpot webhook: no integration found for org %s", resolved_org_id)
                continue

            creds = decrypt_payload(integ.credentials_encrypted)
            access_token = creds.get("access_token") or creds.get("token")
            if not access_token:
                logger.warning("HubSpot webhook: no access_token for org %s", resolved_org_id)
                continue

            # Determine object type
            entity = subscription_type.split(".")[0] if "." in subscription_type else None
            hs_object_type = _HUBSPOT_OBJECT_TYPE_MAP.get(entity or "")
            if not hs_object_type or object_id is None:
                continue

            hs_data = await _fetch_hubspot_object(hs_object_type, object_id, access_token)
            if hs_data is None:
                continue

            props = hs_data.get("properties") or {}

            if hs_object_type == "contacts":
                await _upsert_hubspot_contact(resolved_org_id, object_id, props, session)
            elif hs_object_type == "deals":
                await _upsert_hubspot_deal(resolved_org_id, object_id, props, session)
            elif hs_object_type == "companies":
                await _upsert_hubspot_company(resolved_org_id, object_id, props, session)

            await session.commit()

        except Exception as exc:
            logger.exception("HubSpot webhook: error processing event: %s", exc)

    return {"status": "accepted"}


@router.post("/salesforce")
async def salesforce_webhook(
    request: Request,
    x_salesforce_signature: str | None = Header(default=None),
    org_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    body = await request.body()
    _verify_signature(body, x_salesforce_signature)

    try:
        import json

        payload: dict[str, Any] = json.loads(body)
    except Exception:
        logger.warning("Salesforce webhook: could not parse body")
        return {"status": "accepted"}

    try:
        object_type: str = payload.get("object_type", "")
        object_id: str = payload.get("object_id", "")
        instance_url_hint: str = payload.get("instance_url", "")

        if not object_type or not object_id:
            return {"status": "accepted"}

        # Resolve org
        resolved_org_id = org_id
        if resolved_org_id is None and instance_url_hint:
            resolved_org_id = await _resolve_org_by_instance(instance_url_hint, session)
        if resolved_org_id is None:
            logger.warning("Salesforce webhook: cannot resolve org")
            return {"status": "accepted"}

        from uuid import UUID

        integ_repo = IntegrationRepository(session)
        integ = await integ_repo.get_by_provider(
            org_id=UUID(resolved_org_id), provider="salesforce"
        )
        if integ is None or not integ.credentials_encrypted:
            logger.warning("Salesforce webhook: no integration for org %s", resolved_org_id)
            return {"status": "accepted"}

        creds = decrypt_payload(integ.credentials_encrypted)
        access_token = creds.get("access_token") or creds.get("token")
        instance_url = creds.get("instance_url") or instance_url_hint
        if not access_token or not instance_url:
            logger.warning("Salesforce webhook: missing credentials for org %s", resolved_org_id)
            return {"status": "accepted"}

        sf_data = await _fetch_salesforce_object(
            instance_url, access_token, object_type, object_id
        )
        if sf_data is None:
            return {"status": "accepted"}

        sobject_lower = object_type.lower()
        if "contact" in sobject_lower:
            props = {
                "email": sf_data.get("Email", ""),
                "firstname": sf_data.get("FirstName", ""),
                "lastname": sf_data.get("LastName", ""),
            }
            await _upsert_hubspot_contact(resolved_org_id, object_id, props, session)
        elif "opportunity" in sobject_lower or "deal" in sobject_lower:
            props = {
                "dealname": sf_data.get("Name", ""),
                "dealstage": sf_data.get("StageName", "prospecting"),
                "amount": sf_data.get("Amount", 0),
            }
            await _upsert_hubspot_deal(resolved_org_id, object_id, props, session)
        elif "account" in sobject_lower or "company" in sobject_lower:
            props = {
                "name": sf_data.get("Name", ""),
                "domain": sf_data.get("Website", None),
                "industry": sf_data.get("Industry", None),
                "numberofemployees": sf_data.get("NumberOfEmployees", None),
            }
            await _upsert_hubspot_company(resolved_org_id, object_id, props, session)

        await session.commit()

    except Exception as exc:
        logger.exception("Salesforce webhook: error processing event: %s", exc)

    return {"status": "accepted"}


@router.post("/gmail-reply")
async def gmail_reply_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Handle Gmail push notifications for new messages (reply tracking)."""
    try:
        import base64
        import json

        body_bytes = await request.body()
        notification: dict[str, Any] = json.loads(body_bytes)

        # Gmail push notifications wrap the data in a base64-encoded message
        message_data = notification.get("message", {})
        encoded_data = message_data.get("data", "")
        if encoded_data:
            decoded = base64.urlsafe_b64decode(encoded_data + "==")
            gmail_payload: dict[str, Any] = json.loads(decoded)
        else:
            gmail_payload = notification

        # Extract thread_id or message_id for matching
        thread_id = str(gmail_payload.get("threadId") or gmail_payload.get("thread_id") or "")
        message_id = str(gmail_payload.get("messageId") or gmail_payload.get("message_id") or "")

        matched = False
        if thread_id:
            matched = await _mark_replied_by_external_ref(thread_id, "gmail_thread_id", session)
        if not matched and message_id:
            matched = await _mark_replied_by_external_ref(
                message_id, "gmail_message_id", session
            )
        if not matched:
            logger.debug("Gmail reply webhook: no matching sequence for threadId=%s", thread_id)
    except Exception as exc:
        logger.warning("Gmail reply webhook error: %s", exc)

    return {"status": "accepted"}


@router.post("/outlook-reply")
async def outlook_reply_webhook(
    request: Request,
    validation_token: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Handle Outlook/Graph subscription notifications for reply tracking."""
    # Microsoft Graph requires returning the validationToken as plain text during subscription
    if validation_token:
        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(content=validation_token)

    try:
        import json

        body_bytes = await request.body()
        notification: dict[str, Any] = json.loads(body_bytes)

        # Graph sends an array of change notifications under "value"
        notifications: list[dict[str, Any]] = notification.get("value", [notification])

        for note in notifications:
            resource_data = note.get("resourceData") or {}
            # Outlook conversation/thread tracking
            conversation_id = str(
                resource_data.get("conversationId")
                or note.get("conversationId")
                or ""
            )
            internet_message_id = str(
                resource_data.get("internetMessageId")
                or note.get("internetMessageId")
                or ""
            )
            message_id = str(resource_data.get("id") or note.get("id") or "")

            matched = False
            if conversation_id:
                matched = await _mark_replied_by_external_ref(
                    conversation_id, "outlook_conversation_id", session
                )
            if not matched and internet_message_id:
                matched = await _mark_replied_by_external_ref(
                    internet_message_id, "outlook_message_id", session
                )
            if not matched and message_id:
                matched = await _mark_replied_by_external_ref(
                    message_id, "outlook_resource_id", session
                )
            if not matched:
                logger.debug(
                    "Outlook reply webhook: no matching sequence for conversationId=%s",
                    conversation_id,
                )
    except Exception as exc:
        logger.warning("Outlook reply webhook error: %s", exc)

    return {"status": "accepted"}
