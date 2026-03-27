from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any, Callable

try:  # pragma: no cover - optional dependency path
    from celery import Celery
except Exception:  # pragma: no cover
    Celery = None  # type: ignore[assignment]


@dataclass(slots=True)
class _AsyncResult:
    id: str
    result: Any = None


class _LocalTask:
    def __init__(self, func: Callable[..., Any], name: str) -> None:
        self.func = func
        self.name = name

    def apply_async(self, kwargs: dict[str, Any] | None = None) -> _AsyncResult:
        return _AsyncResult(id=uuid.uuid4().hex, result=self.func(**(kwargs or {})))

    def delay(self, *args: Any, **kwargs: Any) -> _AsyncResult:
        if args:
            raise TypeError("Local task runner only accepts keyword arguments")
        return self.apply_async(kwargs=kwargs)

    __call__ = apply_async


class _LocalCeleryApp:
    def __init__(self) -> None:
        self.conf = type("Config", (), {})()
        self.tasks: dict[str, _LocalTask] = {}

    def task(self, name: str | None = None, **_kwargs: Any):
        def decorator(func: Callable[..., Any]) -> _LocalTask:
            task_name = name or func.__name__
            task = _LocalTask(func, task_name)
            self.tasks[task_name] = task
            return task

        return decorator


def make_celery_app():
    if Celery is None:
        app = _LocalCeleryApp()
        app.conf.update = lambda **kwargs: None  # type: ignore[attr-defined]
        return app
    broker_url = os.getenv("CELERY_BROKER_URL", "memory://")
    backend_url = os.getenv("CELERY_RESULT_BACKEND", "cache+memory://")
    app = Celery("gtm_engine", broker=broker_url, backend=backend_url, include=["backend.workers.tasks"])
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true",
        beat_schedule={
            "weekly-digest": {
                "task": "backend.workers.tasks.weekly_digest",
                "schedule": 60 * 60 * 24 * 7,
            },
            "sync-crm": {
                "task": "backend.workers.tasks.sync_crm",
                "schedule": 60 * 60 * 24,
            },
            "send-approved-sequences": {
                "task": "backend.workers.tasks.send_approved_sequences",
                "schedule": 60 * 15,  # every 15 minutes
            },
            "batch-score": {
                "task": "backend.workers.tasks.batch_score",
                "schedule": 60 * 60,  # every hour
            },
        },
    )
    return app


celery_app = make_celery_app()
