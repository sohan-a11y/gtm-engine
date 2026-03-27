from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db_session, get_org_id
from backend.api.schemas.common import PaginationParams
from backend.api.schemas.integrations import (
    IntegrationConnectRequest,
    IntegrationListResponse,
    IntegrationResponse,
    IntegrationSyncResult,
)
from backend.services import integration_service

router = APIRouter(prefix="/integrations", tags=["integrations"])

_HUBSPOT_AUTH_URL = "https://app.hubspot.com/oauth/authorize"
_HUBSPOT_TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
_HUBSPOT_SCOPES = "crm.objects.contacts.read crm.objects.contacts.write crm.objects.companies.read crm.objects.deals.read"


@router.get("", response_model=IntegrationListResponse)
async def list_integrations(
    org_id: str = Depends(get_org_id),
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> IntegrationListResponse:
    integrations = await integration_service.list_integrations(org_id, session=session)
    start = (pagination.page - 1) * pagination.page_size
    items = integrations[start : start + pagination.page_size]
    return IntegrationListResponse(items=items, total=len(integrations), page=pagination.page, page_size=pagination.page_size)


@router.post("", response_model=IntegrationResponse)
async def connect_integration(
    request: IntegrationConnectRequest,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> IntegrationResponse:
    return await integration_service.connect(org_id, request, session=session)


@router.post("/{provider}/connect", response_model=IntegrationResponse)
async def connect_provider(
    provider: str,
    body: dict[str, Any] = Body(default_factory=dict),
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> IntegrationResponse:
    if not body:
        raise HTTPException(status_code=422, detail="credentials required")
    request = IntegrationConnectRequest(provider=provider, credentials=body)
    return await integration_service.connect(org_id, request, session=session)


@router.post("/{integration_id}/sync", response_model=IntegrationSyncResult)
async def sync_integration(
    integration_id: str,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> IntegrationSyncResult:
    return await integration_service.sync(org_id, integration_id, session=session)


@router.delete("/{integration_id}", response_model=IntegrationResponse)
async def disconnect_integration(
    integration_id: str,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> IntegrationResponse:
    return await integration_service.disconnect(org_id, integration_id, session=session)


# ── HubSpot OAuth ─────────────────────────────────────────────────────────────

@router.get("/hubspot/authorize")
async def hubspot_authorize(org_id: str = Depends(get_org_id)) -> RedirectResponse:
    """Redirect user to HubSpot OAuth consent screen."""
    client_id = os.getenv("HUBSPOT_CLIENT_ID", "")
    redirect_uri = os.getenv("HUBSPOT_REDIRECT_URI", "http://localhost:8000/integrations/hubspot/callback")
    if not client_id:
        raise HTTPException(status_code=503, detail="HUBSPOT_CLIENT_ID not configured")
    url = (
        f"{_HUBSPOT_AUTH_URL}"
        f"?client_id={client_id}"
        f"&scope={_HUBSPOT_SCOPES.replace(' ', '%20')}"
        f"&redirect_uri={redirect_uri}"
        f"&state={org_id}"
    )
    return RedirectResponse(url=url, status_code=302)


@router.get("/hubspot/callback")
async def hubspot_callback(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_db_session),
) -> IntegrationResponse:
    """Exchange OAuth code for tokens and store the integration."""
    client_id = os.getenv("HUBSPOT_CLIENT_ID", "")
    client_secret = os.getenv("HUBSPOT_CLIENT_SECRET", "")
    redirect_uri = os.getenv("HUBSPOT_REDIRECT_URI", "http://localhost:8000/integrations/hubspot/callback")
    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="HubSpot OAuth credentials not configured")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _HUBSPOT_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            tokens = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"HubSpot token exchange failed: {exc}") from exc

    request = IntegrationConnectRequest(
        provider="hubspot",
        credentials={
            "access_token": tokens.get("access_token", ""),
            "refresh_token": tokens.get("refresh_token", ""),
            "expires_in": tokens.get("expires_in", 1800),
        },
    )
    return await integration_service.connect(state, request, session=session)


# ── Salesforce OAuth ──────────────────────────────────────────────────────────

_SF_AUTH_URL = "https://login.salesforce.com/services/oauth2/authorize"
_SF_TOKEN_URL = "https://login.salesforce.com/services/oauth2/token"
_SF_SCOPES = "api refresh_token offline_access"

@router.get("/salesforce/authorize")
async def salesforce_authorize(org_id: str = Depends(get_org_id)) -> RedirectResponse:
    """Redirect user to Salesforce OAuth consent screen."""
    client_id = os.getenv("SALESFORCE_CLIENT_ID", "")
    redirect_uri = os.getenv("SALESFORCE_REDIRECT_URI", "http://localhost:8000/integrations/salesforce/callback")
    if not client_id:
        raise HTTPException(status_code=503, detail="SALESFORCE_CLIENT_ID not configured")
    url = (
        f"{_SF_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={_SF_SCOPES.replace(' ', '%20')}"
        f"&state={org_id}"
    )
    return RedirectResponse(url=url, status_code=302)


@router.get("/salesforce/callback")
async def salesforce_callback(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_db_session),
) -> IntegrationResponse:
    """Exchange OAuth code for Salesforce tokens and store the integration."""
    client_id = os.getenv("SALESFORCE_CLIENT_ID", "")
    client_secret = os.getenv("SALESFORCE_CLIENT_SECRET", "")
    redirect_uri = os.getenv("SALESFORCE_REDIRECT_URI", "http://localhost:8000/integrations/salesforce/callback")
    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="Salesforce OAuth credentials not configured")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _SF_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            tokens = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Salesforce token exchange failed: {exc}") from exc

    request = IntegrationConnectRequest(
        provider="salesforce",
        credentials={
            "access_token": tokens.get("access_token", ""),
            "refresh_token": tokens.get("refresh_token", ""),
            "instance_url": tokens.get("instance_url", ""),
        },
    )
    return await integration_service.connect(state, request, session=session)


# ── Gmail OAuth ───────────────────────────────────────────────────────────────

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GMAIL_SCOPES = "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/userinfo.email"


@router.get("/gmail/authorize")
async def gmail_authorize(org_id: str = Depends(get_org_id)) -> RedirectResponse:
    """Redirect user to Google OAuth consent screen for Gmail access."""
    client_id = os.getenv("GMAIL_CLIENT_ID", "")
    redirect_uri = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/integrations/gmail/callback")
    if not client_id:
        raise HTTPException(status_code=503, detail="GMAIL_CLIENT_ID not configured")
    url = (
        f"{_GOOGLE_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={_GMAIL_SCOPES.replace(' ', '%20')}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={org_id}"
    )
    return RedirectResponse(url=url, status_code=302)


@router.get("/gmail/callback")
async def gmail_callback(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_db_session),
) -> IntegrationResponse:
    """Exchange OAuth code for Gmail tokens and store the integration."""
    client_id = os.getenv("GMAIL_CLIENT_ID", "")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET", "")
    redirect_uri = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/integrations/gmail/callback")
    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="Gmail OAuth credentials not configured")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            tokens = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gmail token exchange failed: {exc}") from exc

    from_address = ""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            ui_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens.get('access_token', '')}"},
            )
            if ui_resp.is_success:
                from_address = ui_resp.json().get("email", "")
    except Exception:
        pass

    request = IntegrationConnectRequest(
        provider="gmail",
        credentials={
            "access_token": tokens.get("access_token", ""),
            "refresh_token": tokens.get("refresh_token", ""),
            "expires_in": tokens.get("expires_in", 3600),
            "from_address": from_address,
        },
    )
    return await integration_service.connect(state, request, session=session)


# ── Outlook OAuth ─────────────────────────────────────────────────────────────

_MS_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
_MS_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
_OUTLOOK_SCOPES = "Mail.Send User.Read offline_access"


@router.get("/outlook/authorize")
async def outlook_authorize(org_id: str = Depends(get_org_id)) -> RedirectResponse:
    """Redirect user to Microsoft OAuth consent screen for Outlook access."""
    client_id = os.getenv("OUTLOOK_CLIENT_ID", "")
    redirect_uri = os.getenv("OUTLOOK_REDIRECT_URI", "http://localhost:8000/integrations/outlook/callback")
    if not client_id:
        raise HTTPException(status_code=503, detail="OUTLOOK_CLIENT_ID not configured")
    url = (
        f"{_MS_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={_OUTLOOK_SCOPES.replace(' ', '%20')}"
        f"&response_mode=query"
        f"&state={org_id}"
    )
    return RedirectResponse(url=url, status_code=302)


@router.get("/outlook/callback")
async def outlook_callback(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_db_session),
) -> IntegrationResponse:
    """Exchange OAuth code for Outlook tokens and store the integration."""
    client_id = os.getenv("OUTLOOK_CLIENT_ID", "")
    client_secret = os.getenv("OUTLOOK_CLIENT_SECRET", "")
    redirect_uri = os.getenv("OUTLOOK_REDIRECT_URI", "http://localhost:8000/integrations/outlook/callback")
    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="Outlook OAuth credentials not configured")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _MS_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            tokens = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Outlook token exchange failed: {exc}") from exc

    from_address = ""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            me_resp = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {tokens.get('access_token', '')}"},
            )
            if me_resp.is_success:
                from_address = me_resp.json().get("mail") or me_resp.json().get("userPrincipalName", "")
    except Exception:
        pass

    request = IntegrationConnectRequest(
        provider="outlook",
        credentials={
            "access_token": tokens.get("access_token", ""),
            "refresh_token": tokens.get("refresh_token", ""),
            "expires_in": tokens.get("expires_in", 3600),
            "from_address": from_address,
        },
    )
    return await integration_service.connect(state, request, session=session)
