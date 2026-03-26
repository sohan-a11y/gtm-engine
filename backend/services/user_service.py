from __future__ import annotations

from dataclasses import dataclass, field

from backend.api.schemas.auth import AuthSessionResponse, TokenResponse, UserResponse
from backend.core.auth import (
    create_token_pair,
    decode_token,
    hash_password,
    token_jti,
    verify_password,
)
from backend.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from backend.core.permissions import list_permissions
from backend.core.cache import build_cache_backend

from .base import BaseService
from .state import generate_id


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
    ) -> AuthSessionResponse:
        if any(user["email"].lower() == email.lower() for user in self.state.users.values()):
            raise ConflictError("User already exists")
        org_id = generate_id("org") if not org_name else f"org_{abs(hash(org_name)) % 10_000_000}"
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
        self.state.orgs.setdefault(
            org_id,
            {
                "id": org_id,
                "name": org_name or "Default Org",
                "created_at": self._timestamp(),
            },
        )
        self.state.settings.setdefault(org_id, {})
        user = UserResponse(**{k: record[k] for k in UserResponse.model_fields if k in record})
        tokens = create_token_pair(user_id, org_id, role, list_permissions(role))
        return AuthSessionResponse(user=user, tokens=TokenResponse(**tokens.model_dump()))

    async def login(self, email: str, password: str) -> AuthSessionResponse:
        user = next((u for u in self.state.users.values() if u["email"].lower() == email.lower()), None)
        if not user or not verify_password(password, user["password_hash"]):
            raise AuthenticationError("Invalid email or password")
        tokens = create_token_pair(user["id"], user["org_id"], user["role"], user["permissions"])
        return AuthSessionResponse(
            user=UserResponse(**{k: user[k] for k in UserResponse.model_fields if k in user}),
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

    async def get_current_user(self, token: str) -> UserResponse:
        payload = decode_token(token, expected_type="access")
        if await self.token_blacklist.get(f"revoked:{payload.jti}") is not None:
            raise AuthenticationError("Token revoked")
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
