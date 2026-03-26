from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class GTMError(Exception):
    message: str
    status_code: int = 500
    code: str = "internal_error"

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return self.message


class AuthenticationError(GTMError):
    def __init__(self, message: str = "Authentication failed", code: str = "authentication_failed"):
        super().__init__(message=message, status_code=401, code=code)


class TokenRevokedError(AuthenticationError):
    def __init__(self, message: str = "Token revoked"):
        super().__init__(message=message, code="token_revoked")


class PermissionDeniedError(GTMError):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403, code="permission_denied")


class NotFoundError(GTMError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404, code="not_found")


class ConflictError(GTMError):
    def __init__(self, message: str = "Conflict detected"):
        super().__init__(message=message, status_code=409, code="conflict")


class ValidationError(GTMError):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message=message, status_code=422, code="validation_error")


class RateLimitError(GTMError):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message=message, status_code=429, code="rate_limited")


class DependencyUnavailableError(GTMError):
    def __init__(self, message: str = "Dependency unavailable", code: str = "dependency_unavailable"):
        super().__init__(message=message, status_code=503, code=code)


class ServiceUnavailableError(DependencyUnavailableError):
    def __init__(self, message: str = "Service unavailable"):
        super().__init__(message=message, code="service_unavailable")


class UpstreamError(GTMError):
    def __init__(self, message: str = "Upstream service error", status_code: int = 502):
        super().__init__(message=message, status_code=status_code, code="upstream_error")


class LLMError(UpstreamError):
    def __init__(self, message: str = "LLM request failed"):
        super().__init__(message=message, status_code=502)
        self.code = "llm_error"


class AgentError(GTMError):
    def __init__(self, message: str = "Agent execution failed"):
        super().__init__(message=message, status_code=500, code="agent_error")


class IntegrationError(UpstreamError):
    def __init__(self, message: str = "Integration request failed"):
        super().__init__(message=message, status_code=502)
        self.code = "integration_error"

