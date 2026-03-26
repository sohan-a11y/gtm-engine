from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    org_name: str | None = None
    role: str = "admin"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None = None
    org_id: str
    role: str
    permissions: list[str] = Field(default_factory=list)
    is_active: bool = True


class AuthSessionResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


class LogoutResponse(BaseModel):
    detail: str = "logged_out"
