from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from backend.api.routers import agents, analytics, approvals, campaigns, companies, deals, events, health, integrations, jobs, leads, notifications, settings, webhooks, auth
from backend.core.exceptions import (
    AuthenticationError,
    ConflictError,
    DependencyUnavailableError,
    GTMError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    UpstreamError,
    ValidationError,
)
from backend.core.logging_config import configure_logging, get_logger
from backend.core.metrics import CONTENT_TYPE_LATEST, record_api_request, render_metrics

logger = get_logger("gtm.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    app.state.started_at = time.time()
    try:
        from backend.db.session import build_async_engine
        from backend.db.models import Base
        engine = build_async_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
    except Exception as exc:
        import logging
        logging.getLogger("gtm.api").warning("DB init skipped: %s", exc)
    yield


def _error_response(exc: GTMError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code, "status_code": exc.status_code},
    )


def create_app() -> FastAPI:
    app = FastAPI(title="AI GTM Engine", version="0.1.0", lifespan=lifespan)

    allowed_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOW_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-Request-ID"],
    )

    @app.middleware("http")
    async def _request_metrics(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["x-request-id"] = request_id
            return response
        except Exception as exc:
            logger.exception("unhandled_request_error", extra={"request_id": request_id})
            raise exc
        finally:
            latency = time.perf_counter() - start
            record_api_request(request.method, request.url.path, status_code, latency)

    @app.exception_handler(GTMError)
    async def _handle_gtm_error(_: Request, exc: GTMError):
        return _error_response(exc)

    @app.exception_handler(AuthenticationError)
    async def _handle_auth_error(_: Request, exc: AuthenticationError):
        return _error_response(exc)

    @app.exception_handler(PermissionDeniedError)
    async def _handle_permission_error(_: Request, exc: PermissionDeniedError):
        return _error_response(exc)

    @app.exception_handler(ConflictError)
    async def _handle_conflict_error(_: Request, exc: ConflictError):
        return _error_response(exc)

    @app.exception_handler(NotFoundError)
    async def _handle_not_found_error(_: Request, exc: NotFoundError):
        return _error_response(exc)

    @app.exception_handler(RateLimitError)
    async def _handle_rate_limit_error(_: Request, exc: RateLimitError):
        return _error_response(exc)

    @app.exception_handler(DependencyUnavailableError)
    async def _handle_dependency_error(_: Request, exc: DependencyUnavailableError):
        return _error_response(exc)

    @app.exception_handler(ServiceUnavailableError)
    async def _handle_service_error(_: Request, exc: ServiceUnavailableError):
        return _error_response(exc)

    @app.exception_handler(UpstreamError)
    async def _handle_upstream_error(_: Request, exc: UpstreamError):
        return _error_response(exc)

    @app.exception_handler(ValidationError)
    async def _handle_validation_error(_: Request, exc: ValidationError):
        return _error_response(exc)

    @app.exception_handler(RequestValidationError)
    async def _handle_request_validation_error(_: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors(), "code": "validation_error"})

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(_: Request, exc: Exception):
        logger.exception("unexpected_error", extra={"error": str(exc)})
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "code": "internal_error"},
        )

    app.include_router(auth.router)
    app.include_router(leads.router)
    app.include_router(companies.router)
    app.include_router(deals.router)
    app.include_router(campaigns.router)
    app.include_router(approvals.router)
    app.include_router(agents.router)
    app.include_router(analytics.router)
    app.include_router(integrations.router)
    app.include_router(settings.router)
    app.include_router(webhooks.router)
    app.include_router(jobs.router)
    app.include_router(notifications.router)
    app.include_router(events.router)
    app.include_router(health.router)

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {"status": "ok", "service": "ai-gtm-engine", "version": app.version}

    @app.get("/metrics")
    async def metrics() -> Response:
        payload, content_type = render_metrics()
        return Response(content=payload, media_type=content_type or CONTENT_TYPE_LATEST)

    return app


app = create_app()

