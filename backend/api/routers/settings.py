from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_org_id
from backend.api.schemas.settings import BrandVoiceSettings, LLMConfig, OrgSettings
from backend.services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=OrgSettings)
async def get_settings(org_id: str = Depends(get_org_id)) -> OrgSettings:
    return await settings_service.get_settings(org_id)


@router.patch("", response_model=OrgSettings)
async def update_settings(request: OrgSettings, org_id: str = Depends(get_org_id)) -> OrgSettings:
    return await settings_service.update_settings(org_id, request)


@router.get("/llm-config", response_model=LLMConfig)
async def get_llm_config(org_id: str = Depends(get_org_id)) -> LLMConfig:
    return (await settings_service.get_settings(org_id)).llm


@router.patch("/llm-config", response_model=LLMConfig)
async def update_llm_config(request: LLMConfig, org_id: str = Depends(get_org_id)) -> LLMConfig:
    settings = await settings_service.get_settings(org_id)
    settings.llm = request
    return (await settings_service.update_settings(org_id, settings)).llm


@router.get("/brand-voice", response_model=BrandVoiceSettings)
async def get_brand_voice(org_id: str = Depends(get_org_id)) -> BrandVoiceSettings:
    return (await settings_service.get_settings(org_id)).brand_voice


@router.patch("/brand-voice", response_model=BrandVoiceSettings)
async def update_brand_voice(request: BrandVoiceSettings, org_id: str = Depends(get_org_id)) -> BrandVoiceSettings:
    settings = await settings_service.get_settings(org_id)
    settings.brand_voice = request
    return (await settings_service.update_settings(org_id, settings)).brand_voice

