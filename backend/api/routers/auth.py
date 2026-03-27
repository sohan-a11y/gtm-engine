from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user, get_db_session
from backend.api.schemas.auth import AuthSessionResponse, LoginRequest, LogoutResponse, RefreshRequest, RegisterRequest, UserResponse
from backend.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthSessionResponse)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthSessionResponse:
    return await user_service.register(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        org_name=request.org_name,
        role=request.role,
        session=session,
    )


@router.post("/login", response_model=AuthSessionResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthSessionResponse:
    return await user_service.login(email=request.email, password=request.password, session=session)


@router.post("/refresh", response_model=AuthSessionResponse)
async def refresh(request: RefreshRequest) -> AuthSessionResponse:
    return await user_service.refresh(request.refresh_token)


@router.post("/logout", response_model=LogoutResponse)
async def logout(current_user: UserResponse = Depends(get_current_user)) -> LogoutResponse:
    await user_service.logout(current_user.id)
    return LogoutResponse()
