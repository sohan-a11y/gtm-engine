from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

from .exceptions import DependencyUnavailableError


class SecretProvider(ABC):
    @abstractmethod
    def get_secret(self, name: str, default: str | None = None) -> str | None: ...

    def set_secret(self, name: str, value: str) -> None:  # pragma: no cover - optional path
        raise NotImplementedError


@dataclass(slots=True)
class EnvSecretProvider(SecretProvider):
    def get_secret(self, name: str, default: str | None = None) -> str | None:
        return os.getenv(name, default)


@dataclass(slots=True)
class VaultSecretProvider(SecretProvider):
    base_url: str
    token: str
    mount: str = "secret"

    def _headers(self) -> dict[str, str]:
        return {"X-Vault-Token": self.token}

    def get_secret(self, name: str, default: str | None = None) -> str | None:
        url = f"{self.base_url.rstrip('/')}/v1/{self.mount}/data/{name}"
        try:
            response = httpx.get(url, headers=self._headers(), timeout=10.0)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return payload.get("data", {}).get("data", {}).get("value", default)
        except Exception as exc:  # pragma: no cover - external path
            raise DependencyUnavailableError("Vault secret lookup failed", code="vault_lookup_failed") from exc

    def set_secret(self, name: str, value: str) -> None:  # pragma: no cover - external path
        url = f"{self.base_url.rstrip('/')}/v1/{self.mount}/data/{name}"
        payload = {"data": {"value": value}}
        try:
            response = httpx.post(url, json=payload, headers=self._headers(), timeout=10.0)
            response.raise_for_status()
        except Exception as exc:
            raise DependencyUnavailableError("Vault secret write failed", code="vault_write_failed") from exc


def get_secret_provider() -> SecretProvider:
    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")
    if vault_addr and vault_token:
        return VaultSecretProvider(base_url=vault_addr, token=vault_token)
    return EnvSecretProvider()


def resolve_secret(name: str, default: str | None = None) -> str | None:
    return get_secret_provider().get_secret(name, default)

