from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .exceptions import DependencyUnavailableError


def _derive_key(raw_value: str) -> bytes:
    try:
        decoded = base64.urlsafe_b64decode(raw_value.encode("utf-8"))
        if len(decoded) == 32:
            return decoded
    except Exception:
        pass
    return hashlib.sha256(raw_value.encode("utf-8")).digest()


@dataclass(slots=True)
class EncryptionService:
    key: bytes

    def encrypt(self, value: str) -> str:
        nonce = os.urandom(12)
        aesgcm = AESGCM(self.key)
        ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), None)
        return base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt(self, value: str) -> str:
        try:
            decoded = base64.urlsafe_b64decode(value.encode("utf-8"))
            nonce, ciphertext = decoded[:12], decoded[12:]
            aesgcm = AESGCM(self.key)
            return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
        except Exception as exc:  # pragma: no cover - defensive
            raise DependencyUnavailableError("Unable to decrypt payload", code="decryption_failed") from exc

    def encrypt_json(self, value: Any) -> str:
        return self.encrypt(json.dumps(value, separators=(",", ":"), sort_keys=True))

    def decrypt_json(self, value: str) -> Any:
        return json.loads(self.decrypt(value))


def _build_service() -> EncryptionService:
    secret = os.getenv("ENCRYPTION_KEY") or os.getenv("DEV_ENCRYPTION_KEY") or "dev-encryption-key"
    return EncryptionService(key=_derive_key(secret))


ENCRYPTION_SERVICE = _build_service()


def encrypt_value(value: str) -> str:
    return ENCRYPTION_SERVICE.encrypt(value)


def decrypt_value(value: str) -> str:
    return ENCRYPTION_SERVICE.decrypt(value)


def encrypt_payload(value: Any) -> str:
    return ENCRYPTION_SERVICE.encrypt_json(value)


def decrypt_payload(value: str) -> Any:
    return ENCRYPTION_SERVICE.decrypt_json(value)

