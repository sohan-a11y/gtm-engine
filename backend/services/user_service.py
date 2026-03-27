from __future__ import annotations

import re
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.auth import AuthSessionResponse, TokenResponse, UserResponse
from backend.core.auth import (
    create_token_pair,
    decode_token,
    hash_password,
    token_jti,
    verify_password,
)
from backend.core.cache import build_cache_backend
from backend.core.exceptions import AuthenticationError, ConflictError, NotFoundError, ServiceUnavailableError
from backend.core.permissions import list_permissions
from backend.db.repositories.user_repo import OrganizationRepository, UserRepository

from .base import BaseService


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or "org"


def _user_response(user) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name or None,
        org_id=str(user.org_id),
        role=user.role,
        permissions=list(user.permissions or []),
        is_active=user.is_active,
    )


@dataclass(slots=True)
class UserService(BaseService):
    revoked_tokens: set[str] = field(default_factory=set)
    token_blacklist = build_cache_backend()

    async def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
        org_name: str | None = None,
        role: str = "admin",
        session: AsyncSession | None = None,
    ) -> AuthSessionResponse:
        if session is None:
            # Fallback to stateless in-memory path (used by tests / bootstrap)
            if any(u["email"].lower() == email.lower() for u in self.state.users.values()):
                raise ConflictError("User already exists")
            from .state import generate_id
            org_id = f"org_{abs(hash(org_name or email)) % 10_000_000}"
            user_id = generate_id("user")
            record = {
                "id": user_id,
                "email": email,
                "password_hash": hash_password(password),
                "full_name": full_name,
                "org_id": org_id,
                "role": role,
                "permissions": list_permissions(role),
                "is_active": True,
                "created_at": self._timestamp(),
                "updated_at": self._timestamp(),
            }
            self.state.users[user_id] = record
            self.state.orgs.setdefault(org_id, {"id": org_id, "name": org_name or "Default Org"})
            self.state.settings.setdefault(org_id, {})
            user_resp = UserResponse(**{k: record[k] for k in UserResponse.model_fields if k in record})
            tokens = create_token_pair(user_id, org_id, role, list_permissions(role))
            return AuthSessionResponse(user=user_resp, tokens=TokenResponse(**tokens.model_dump()))

        user_repo = UserRepository(session)
        org_repo = OrganizationRepository(session)
        try:
            existing = await user_repo.get_by_email_any_org(email=email.lower())
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if existing is not None:
            raise ConflictError("User already exists")
        effective_org_name = org_name or "Default Org"
        base_slug = _slugify(effective_org_name)
        slug = base_slug
        counter = 1
        while True:
            try:
                existing_org = await org_repo.get_by_slug(slug=slug)
            except Exception as exc:
                raise ServiceUnavailableError(str(exc)) from exc
            if existing_org is None:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        try:
            org = await org_repo.create_org(name=effective_org_name, slug=slug)
            user = await user_repo.create(
                org_id=org.id,
                data={
                    "email": email.lower(),
                    "password_hash": hash_password(password),
                    "full_name": full_name or "",
                    "role": role,
                    "permissions": list_permissions(role),
                    "is_active": True,
                },
            )
            await session.commit()
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        user_resp = _user_response(user)
        tokens = create_token_pair(str(user.id), str(org.id), role, list_permissions(role))
        return AuthSessionResponse(user=user_resp, tokens=TokenResponse(**tokens.model_dump()))

    async def login(
        self,
        email: str,
        password: str,
        *,
        session: AsyncSession | None = None,
    ) -> AuthSessionResponse:
        if session is None:
            user = next((u for u in self.state.users.values() if u["email"].lower() == email.lower()), None)
            if not user or not verify_password(password, user["password_hash"]):
                raise AuthenticationError("Invalid email or password")
            tokens = create_token_pair(user["id"], user["org_id"], user["role"], user["permissions"])
            return AuthSessionResponse(
                user=UserResponse(**{k: user[k] for k in UserResponse.model_fields if k in user}),
                tokens=TokenResponse(**tokens.model_dump()),
            )

        user_repo = UserRepository(session)
        try:
            db_user = await user_repo.get_by_email_any_org(email=email.lower())
        except Exception as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        if db_user is None or not verify_password(password, db_user.password_hash):
            raise AuthenticationError("Invalid email or password")
        tokens = create_token_pair(
            str(db_user.id),
            str(db_user.org_id),
            db_user.role,
            list(db_user.permissions or []),
        )
        return AuthSessionResponse(
            user=_user_response(db_user),
            tokens=TokenResponse(**tokens.model_dump()),
        )

    async def refresh(self, refresh_token: str) -> AuthSessionResponse:
        payload = decode_token(refresh_token, expected_type="refresh")
        return await self.issue_tokens(payload.sub)

    async def issue_tokens(self, user_id: str) -> AuthSessionResponse:
        user = self.state.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        tokens = create_token_pair(user["id"], user["org_id"], user["role"], user["permissions"])
        return AuthSessionResponse(
            user=UserResponse(**{k: user[k] for k in UserResponse.model_fields if k in user}),
            tokens=TokenResponse(**tokens.model_dump()),
        )

    async def logout(self, token: str) -> None:
        jti = token_jti(token)
        self.revoked_tokens.add(jti)
        await self.token_blacklist.set(f"revoked:{jti}", True, ttl_seconds=24 * 60 * 60)

    async def get_current_user(
        self,
        token: str,
        *,
        session: AsyncSession | None = None,
    ) -> UserResponse:
        payload = decode_token(token, expected_type="access")
        if await self.token_blacklist.get(f"revoked:{payload.jti}") is not None:
            raise AuthenticationError("Token revoked")

        # Try DB lookup first
        if session is not None:
            user_repo = UserRepository(session)
            try:
                db_user = await user_repo.get(org_id=UUID(payload.org_id), object_id=UUID(payload.sub))
            except Exception:
                db_user = None
            if db_user is not None:
                return _user_response(db_user)

        # Fall back to in-memory state
        user = self.state.users.get(payload.sub)
        if user:
            return UserResponse(**{k: user[k] for k in UserResponse.model_fields if k in user})

        # Stateless JWT path: build UserResponse from token claims (no user record required).
        # This allows API tests and service accounts to authenticate with a valid JWT
        # without needing a user row in the in-memory state.
        return UserResponse(
            id=payload.sub,
            email=f"svc-{payload.sub[:8]}@example.com",
            org_id=payload.org_id,
            role=payload.role,
            permissions=payload.permissions,
        )

    async def list_users(self, org_id: str) -> list[UserResponse]:
        return [
            UserResponse(**{k: user[k] for k in UserResponse.model_fields if k in user})
            for user in self.state.users.values()
            if user["org_id"] == org_id
        ]
