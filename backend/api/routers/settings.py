from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db_session, get_org_id
from backend.api.schemas.settings import BrandVoiceSettings, LLMConfig, OrgSettings
from backend.services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=OrgSettings)
async def get_settings(
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> OrgSettings:
    return await settings_service.get_settings(org_id, session=session)


@router.patch("", response_model=OrgSettings)
async def update_settings(
    request: OrgSettings,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> OrgSettings:
    return await settings_service.update_settings(org_id, request, session=session)


@router.get("/llm-config", response_model=LLMConfig)
async def get_llm_config(
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> LLMConfig:
    return (await settings_service.get_settings(org_id, session=session)).llm


@router.patch("/llm-config", response_model=LLMConfig)
async def update_llm_config(
    request: LLMConfig,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> LLMConfig:
    settings = await settings_service.get_settings(org_id, session=session)
    settings.llm = request
    return (await settings_service.update_settings(org_id, settings, session=session)).llm


@router.get("/brand-voice", response_model=BrandVoiceSettings)
async def get_brand_voice(
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> BrandVoiceSettings:
    return (await settings_service.get_settings(org_id, session=session)).brand_voice


@router.patch("/brand-voice", response_model=BrandVoiceSettings)
async def update_brand_voice(
    request: BrandVoiceSettings,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> BrandVoiceSettings:
    settings = await settings_service.get_settings(org_id, session=session)
    settings.brand_voice = request
    return (await settings_service.update_settings(org_id, settings, session=session)).brand_voice
