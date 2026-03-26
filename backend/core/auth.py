from __future__ import annotations

import base64
import hashlib
import hmac
import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

try:  # pragma: no cover - optional dependency path
    from jose import JWTError, jwt
except Exception:  # pragma: no cover
    class JWTError(Exception):
        pass

    class _FallbackJWT:
        @staticmethod
        def encode(payload: dict[str, Any], secret: str, algorithm: str = "HS256") -> str:
            header = {"alg": algorithm, "typ": "JWT"}
            header_b64 = base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode()).decode().rstrip("=")
            payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":"), default=str).encode()).decode().rstrip("=")
            signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
            signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
            return f"{header_b64}.{payload_b64}.{signature_b64}"

        @staticmethod
        def decode(token: str, secret: str, algorithms: list[str] | None = None) -> dict[str, Any]:
            try:
                header_b64, payload_b64, signature_b64 = token.split(".")
            except ValueError as exc:
                raise JWTError("Invalid token format") from exc
            signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
            actual = base64.urlsafe_b64decode(signature_b64 + "==")
            if not hmac.compare_digest(expected, actual):
                raise JWTError("Invalid token signature")
            payload_json = base64.urlsafe_b64decode(payload_b64 + "==").decode("utf-8")
            return json.loads(payload_json)

    jwt = _FallbackJWT()

try:  # pragma: no cover - optional dependency path
    from passlib.context import CryptContext
except Exception:  # pragma: no cover
    class CryptContext:  # type: ignore[no-redef]
        def __init__(self, *_, **__):
            self.iterations = 390_000

        def hash(self, password: str) -> str:
            salt = secrets.token_hex(16)
            digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), self.iterations)
            return f"pbkdf2_sha256${self.iterations}${salt}${base64.urlsafe_b64encode(digest).decode()}"

        def verify(self, plain: str, hashed: str) -> bool:
            try:
                algorithm, iterations, salt, expected = hashed.split("$", 3)
                if algorithm != "pbkdf2_sha256":
                    return False
                digest = hashlib.pbkdf2_hmac(
                    "sha256",
                    plain.encode("utf-8"),
                    salt.encode("utf-8"),
                    int(iterations),
                )
                return hmac.compare_digest(base64.urlsafe_b64encode(digest).decode(), expected)
            except Exception:
                return False

from pydantic import BaseModel, Field

from .exceptions import AuthenticationError, TokenRevokedError

JWT_SECRET = os.getenv("JWT_SECRET") or "dev-jwt-secret-change-me"
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    sub: str
    org_id: str
    role: str = "viewer"
    permissions: list[str] = Field(default_factory=list)
    jti: str = ""
    type: str = "access"
    iat: int = 0
    exp: int = 0


class TokenBundle(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _encode_payload(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_payload(token: str) -> dict[str, Any]:
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:  # pragma: no cover - exercised through dependency layer
        raise AuthenticationError("Invalid token") from exc
    if data.get("jti") and data.get("jti") == "revoked":
        raise TokenRevokedError()
    return data


def create_access_token(user_id: str, org_id: str, role: str, permissions: list[str]) -> str:
    issued_at = _now()
    expires_at = issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "org_id": org_id,
        "role": role,
        "permissions": permissions,
        "jti": uuid4().hex,
        "type": "access",
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return _encode_payload(payload)


def create_refresh_token(user_id: str, org_id: str) -> str:
    issued_at = _now()
    expires_at = issued_at + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "org_id": org_id,
        "jti": uuid4().hex,
        "type": "refresh",
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return _encode_payload(payload)


def create_token_pair(user_id: str, org_id: str, role: str, permissions: list[str]) -> TokenBundle:
    access_token = create_access_token(user_id, org_id, role, permissions)
    refresh_token = create_refresh_token(user_id, org_id)
    return TokenBundle(access_token=access_token, refresh_token=refresh_token)


def decode_token(token: str, expected_type: str | None = "access") -> TokenPayload:
    payload = _decode_payload(token)
    if expected_type and payload.get("type") != expected_type:
        raise AuthenticationError("Unexpected token type")
    return TokenPayload.model_validate(payload)


def token_jti(token: str) -> str:
    return decode_token(token, expected_type=None).jti


def token_fingerprint(token: str) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
