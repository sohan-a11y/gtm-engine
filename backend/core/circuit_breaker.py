from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(slots=True)
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 120
    success_threshold: int = 3
    failures: int = 0
    successes: int = 0
    opened_at: float | None = None
    _state: str = field(default="closed", init=False)

    @property
    def state(self) -> str:
        if self._state == "open" and self.opened_at is not None:
            if time.time() - self.opened_at >= self.recovery_timeout_seconds:
                self._state = "half_open"
                self.successes = 0
        return self._state

    def allow_request(self) -> bool:
        return self.state != "open"

    def record_success(self) -> None:
        if self.state == "half_open":
            self.successes += 1
            if self.successes >= self.success_threshold:
                self._state = "closed"
                self.failures = 0
                self.opened_at = None
                self.successes = 0
        else:
            self.failures = 0

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self._state = "open"
            self.opened_at = time.time()
            self.successes = 0


def build_circuit_breaker() -> CircuitBreaker:
    return CircuitBreaker()

