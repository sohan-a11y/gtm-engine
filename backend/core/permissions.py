from __future__ import annotations

from typing import Iterable

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "auth.manage",
        "leads.read",
        "leads.write",
        "campaigns.read",
        "campaigns.write",
        "approvals.read",
        "approvals.write",
        "agents.trigger",
        "analytics.read",
        "integrations.manage",
        "settings.manage",
        "users.manage",
    },
    "member": {
        "leads.read",
        "leads.write",
        "campaigns.read",
        "campaigns.write",
        "approvals.read",
        "approvals.write",
        "agents.trigger",
        "analytics.read",
        "integrations.manage",
    },
    "viewer": {
        "leads.read",
        "campaigns.read",
        "approvals.read",
        "analytics.read",
    },
}


def list_permissions(role: str) -> list[str]:
    return sorted(ROLE_PERMISSIONS.get(role, set()))


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def has_any_permission(role: str, permissions: Iterable[str]) -> bool:
    granted = ROLE_PERMISSIONS.get(role, set())
    return any(permission in granted for permission in permissions)

