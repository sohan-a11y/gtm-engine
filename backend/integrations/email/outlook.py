"""Outlook / Microsoft 365 email integration via Microsoft Graph API.

Docs: https://learn.microsoft.com/en-us/graph/api/user-sendmail

Authentication: OAuth2 Bearer token with the Mail.Send permission.
The token must be acquired via MSAL or delegated OAuth flow before passing
it here; this client does not handle token acquisition.

Deliverability check: same MX-record + format approach as the Gmail client
(no paid API required).
"""
from __future__ import annotations

import logging
import re
import socket
from typing import Any

import httpx

from backend.integrations.email.base_email import BaseEmail

logger = logging.getLogger("gtm.integrations.outlook")

_GRAPH_SEND_URL = "https://graph.microsoft.com/v1.0/me/sendMail"
_TIMEOUT = 20.0
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _mx_exists(domain: str) -> bool:
    try:
        import dns.resolver  # type: ignore[import]
        answers = dns.resolver.resolve(domain, "MX", lifetime=3)
        return len(answers) > 0
    except Exception:
        try:
            socket.getaddrinfo(domain, None)
            return True
        except OSError:
            return False


class OutlookEmailClient(BaseEmail):
    provider_name = "outlook"

    def __init__(
        self,
        *,
        oauth_token: str | None = None,
        from_address: str | None = None,
    ) -> None:
        self.oauth_token = oauth_token
        self.from_address = from_address or ""

    async def send_email(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        from_address: str | None = None,
    ) -> dict[str, Any]:
        if not self.oauth_token:
            logger.warning("Outlook: no oauth_token configured — cannot send email to %s", to)
            return {
                "provider": self.provider_name,
                "to": to,
                "subject": subject,
                "status": "skipped",
                "reason": "no_oauth_token",
            }

        # Microsoft Graph sendMail payload
        payload: dict[str, Any] = {
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": to}}],
            },
            "saveToSentItems": "true",
        }
        sender = from_address or self.from_address
        if sender:
            payload["message"]["from"] = {"emailAddress": {"address": sender}}

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    _GRAPH_SEND_URL,
                    headers={
                        "Authorization": f"Bearer {self.oauth_token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()
                # Graph returns 202 Accepted with empty body on success
                return {
                    "provider": self.provider_name,
                    "to": to,
                    "subject": subject,
                    "from_address": sender,
                    "status": "sent",
                }
        except httpx.HTTPStatusError as exc:
            logger.error("Outlook send HTTP %s: %s", exc.response.status_code, exc.response.text[:200])
            return {
                "provider": self.provider_name,
                "to": to,
                "status": "error",
                "detail": f"HTTP {exc.response.status_code}",
            }
        except Exception as exc:
            logger.error("Outlook send error: %s", exc)
            return {"provider": self.provider_name, "to": to, "status": "error", "detail": str(exc)}

    async def check_deliverability(self, *, email: str) -> dict[str, Any]:
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
