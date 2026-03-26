"""Gmail email integration via the Gmail REST API.

Docs: https://developers.google.com/gmail/api/reference/rest/v1/users.messages/send

Authentication: OAuth2 Bearer token with the
``https://www.googleapis.com/auth/gmail.send`` scope.

Messages are sent as RFC 2822 email encoded in URL-safe base64, which is
the format Gmail's API requires.

Deliverability check: Gmail does not expose a verification endpoint, so we
delegate to a lightweight MX + format check using DNS (no third-party API key
required). A real production setup should use Hunter or Apollo for richer
deliverability data.
"""
from __future__ import annotations

import base64
import logging
import re
import socket
from email.mime.text import MIMEText
from typing import Any

import httpx

from backend.integrations.email.base_email import BaseEmail

logger = logging.getLogger("gtm.integrations.gmail")

_GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
_TIMEOUT = 20.0
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _build_raw_message(*, to: str, subject: str, body: str, from_address: str) -> str:
    """Construct RFC 2822 message and base64url-encode it for the Gmail API."""
    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = to
    msg["From"] = from_address
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return raw


def _mx_exists(domain: str) -> bool:
    """Return True if the domain has at least one MX record (best-effort)."""
    try:
        import dns.resolver  # type: ignore[import]
        answers = dns.resolver.resolve(domain, "MX", lifetime=3)
        return len(answers) > 0
    except Exception:
        # Fallback: try a basic socket lookup if dnspython isn't installed
        try:
            socket.getaddrinfo(domain, None)
            return True
        except OSError:
            return False


class GmailEmailClient(BaseEmail):
    provider_name = "gmail"

    def __init__(
        self,
        *,
        oauth_token: str | None = None,
        from_address: str | None = None,
    ) -> None:
        self.oauth_token = oauth_token
        self.from_address = from_address or ""

    # ── send ──────────────────────────────────────────────────────────────────

    async def send_email(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        from_address: str | None = None,
    ) -> dict[str, Any]:
        sender = from_address or self.from_address
        if not self.oauth_token:
            logger.warning("Gmail: no oauth_token configured — cannot send email to %s", to)
            return {
                "provider": self.provider_name,
                "to": to,
                "subject": subject,
                "status": "skipped",
                "reason": "no_oauth_token",
            }
        if not sender:
            logger.warning("Gmail: no from_address configured")
            return {
                "provider": self.provider_name,
                "to": to,
                "subject": subject,
                "status": "error",
                "reason": "no_from_address",
            }

        raw = _build_raw_message(to=to, subject=subject, body=body, from_address=sender)

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    _GMAIL_SEND_URL,
                    headers={
                        "Authorization": f"Bearer {self.oauth_token}",
                        "Content-Type": "application/json",
                    },
                    json={"raw": raw},
                )
                resp.raise_for_status()
                result = resp.json()
                return {
                    "provider": self.provider_name,
                    "to": to,
                    "subject": subject,
                    "from_address": sender,
                    "message_id": result.get("id"),
                    "thread_id": result.get("threadId"),
                    "status": "sent",
                }
        except httpx.HTTPStatusError as exc:
            logger.error("Gmail send HTTP %s: %s", exc.response.status_code, exc.response.text[:200])
            return {
                "provider": self.provider_name,
                "to": to,
                "status": "error",
                "detail": f"HTTP {exc.response.status_code}",
            }
        except Exception as exc:
            logger.error("Gmail send error: %s", exc)
            return {"provider": self.provider_name, "to": to, "status": "error", "detail": str(exc)}

    # ── deliverability ────────────────────────────────────────────────────────

    async def check_deliverability(self, *, email: str) -> dict[str, Any]:
        """
        Lightweight deliverability check:
          1. Validate email format with regex.
          2. Verify the domain has MX records.

        Returns a score in [0.0, 1.0]:
          - 0.0  : invalid format
          - 0.5  : valid format but no MX record found
          - 0.9  : valid format and MX record present
        """
        if not _EMAIL_RE.match(email):
            return {
                "provider": self.provider_name,
                "email": email,
                "score": 0.0,
                "status": "invalid_format",
            }

        domain = email.split("@", 1)[1]
        has_mx = _mx_exists(domain)

        return {
            "provider": self.provider_name,
            "email": email,
            "score": 0.9 if has_mx else 0.5,
            "status": "valid" if has_mx else "no_mx",
        }
