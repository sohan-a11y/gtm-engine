from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user, get_db_session, get_org_id
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


@router.get("/users", response_model=list[UserResponse])
async def list_team(
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> list[UserResponse]:
    return await user_service.list_users(org_id, session=session)


class InviteRequest(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: str = "member"


@router.post("/invite", response_model=UserResponse)
async def invite_user(
    request: InviteRequest,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    return await user_service.invite_user(
        org_id, request.email, request.role, request.full_name, session=session
    )


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_role(
    user_id: str,
    role: str,
    org_id: str = Depends(get_org_id),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    return await user_service.update_user_role(org_id, user_id, role, session=session)
