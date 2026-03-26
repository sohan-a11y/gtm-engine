from __future__ import annotations

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    provider: str = "mock"
    model: str = "mock-model"
    api_key: str | None = None
    temperature: float = 0.2


class BrandVoiceSettings(BaseModel):
    tone: str = "professional"
    vocabulary: list[str] = Field(default_factory=list)
    banned_phrases: list[str] = Field(default_factory=list)


class OrgSettings(BaseModel):
    org_name: str | None = None
    timezone: str = "UTC"
    llm: LLMConfig = Field(default_factory=LLMConfig)
    brand_voice: BrandVoiceSettings = Field(default_factory=BrandVoiceSettings)
    notifications_enabled: bool = True

