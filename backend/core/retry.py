from __future__ import annotations

from dataclasses import dataclass

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential, wait_fixed


@dataclass(slots=True)
class RetryProfile:
    attempts: int
    strategy: str


LLM_RETRY = RetryProfile(attempts=3, strategy="exponential")
ENRICHMENT_RETRY = RetryProfile(attempts=3, strategy="fixed")
CRM_RETRY = RetryProfile(attempts=5, strategy="exponential")
EMAIL_RETRY = RetryProfile(attempts=3, strategy="exponential")


def build_retry_decorator(profile: RetryProfile, *exceptions: type[BaseException]):
    wait = wait_fixed(60) if profile.strategy == "fixed" else wait_exponential(multiplier=2, min=2, max=30)
    return retry(
        reraise=True,
        stop=stop_after_attempt(profile.attempts),
        wait=wait,
        retry=retry_if_exception_type(exceptions or (Exception,)),
    )

