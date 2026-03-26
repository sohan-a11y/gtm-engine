from __future__ import annotations

import os
from functools import lru_cache
from typing import Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.api.schemas.auth import UserResponse
from backend.core.audit_logger import AuditLogger, build_audit_logger
from backend.core.cache import CacheBackend, build_cache_backend
from backend.core.exceptions import AuthenticationError, PermissionDeniedError, RateLimitError
from backend.core.llm_router import LLMRouter, build_llm_router
from backend.core.orchestrator import GTMOrchestrator, build_orchestrator
from backend.core.permissions import has_permission
from backend.core.prompt_manager import PromptManager, build_prompt_manager
from backend.core.rate_limiter import RateLimiter, build_rate_limiter
from backend.services import user_service

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _cache_backend() -> CacheBackend:
    return build_cache_backend(os.getenv("REDIS_URL"))


@lru_cache
def _rate_limiter() -> RateLimiter:
    return build_rate_limiter(_cache_backend())


@lru_cache
def _llm_router() -> LLMRouter:
    return build_llm_router()


@lru_cache
def _prompt_manager() -> PromptManager:
    return build_prompt_manager()


@lru_cache
def _audit_logger() -> AuditLogger:
    return build_audit_logger()


@lru_cache
def _orchestrator() -> GTMOrchestrator:
    return build_orchestrator()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserResponse:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Missing bearer token")
    return await user_service.get_current_user(credentials.credentials)


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserResponse | None:
    if not credentials or credentials.scheme.lower() != "bearer":
        return None
    return await user_service.get_current_user(credentials.credentials)


def get_org_id(current_user: UserResponse = Depends(get_current_user)) -> str:
    return current_user.org_id


def get_user_id(current_user: UserResponse = Depends(get_current_user)) -> str:
    return current_user.id


def require_permission(permission: str) -> Callable[[UserResponse], UserResponse]:
    async def dependency(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if not (permission in current_user.permissions or has_permission(current_user.role, permission)):
            raise PermissionDeniedError(f"Missing permission: {permission}")
        return current_user

    return dependency


def get_rate_limiter() -> RateLimiter:
    return _rate_limiter()


def get_cache() -> CacheBackend:
    return _cache_backend()


def get_llm_router() -> LLMRouter:
    return _llm_router()


def get_prompt_manager() -> PromptManager:
    return _prompt_manager()


def get_audit_logger() -> AuditLogger:
    return _audit_logger()


def get_orchestrator() -> GTMOrchestrator:
    return _orchestrator()


def get_request_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def enforce_rate_limit(
    request: Request,
    rule_name: str,
    current_user: UserResponse | None = None,
    namespace: str = "api",
) -> None:
    subject = current_user.id if current_user else get_request_ip(request)
    limiter = get_rate_limiter()
    result = await limiter.check(subject=subject, rule_name=rule_name, namespace=namespace)
    if not result.allowed:
        raise RateLimitError("Too many requests")

