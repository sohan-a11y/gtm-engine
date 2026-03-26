from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_current_user
from backend.api.schemas.auth import AuthSessionResponse, LoginRequest, LogoutResponse, RefreshRequest, RegisterRequest, UserResponse
from backend.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthSessionResponse)
async def register(request: RegisterRequest) -> AuthSessionResponse:
    return await user_service.register(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        org_name=request.org_name,
        role=request.role,
    )


@router.post("/login", response_model=AuthSessionResponse)
async def login(request: LoginRequest) -> AuthSessionResponse:
    return await user_service.login(email=request.email, password=request.password)


@router.post("/refresh", response_model=AuthSessionResponse)
async def refresh(request: RefreshRequest) -> AuthSessionResponse:
    return await user_service.refresh(request.refresh_token)


@router.post("/logout", response_model=LogoutResponse)
async def logout(current_user: UserResponse = Depends(get_current_user)) -> LogoutResponse:
    await user_service.logout(current_user.id)
    return LogoutResponse()
