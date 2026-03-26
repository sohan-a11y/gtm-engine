"""Unit tests for backend/core/encryption.py"""
from __future__ import annotations

import pytest

from backend.core.encryption import (
    EncryptionService,
    _derive_key,
    decrypt_payload,
    decrypt_value,
    encrypt_payload,
    encrypt_value,
)


# ── key derivation ────────────────────────────────────────────────────────────

def test_derive_key_produces_32_bytes():
    key = _derive_key("any-string-at-all")
    assert len(key) == 32


def test_derive_key_is_deterministic():
    assert _derive_key("same-string") == _derive_key("same-string")


def test_derive_key_differs_for_different_inputs():
    assert _derive_key("key-a") != _derive_key("key-b")


# ── EncryptionService ─────────────────────────────────────────────────────────

@pytest.fixture()
def svc() -> EncryptionService:
    return EncryptionService(key=_derive_key("test-encryption-key"))


def test_encrypt_decrypt_roundtrip(svc):
    original = "my sensitive value"
    ciphertext = svc.encrypt(original)
    assert ciphertext != original
    assert svc.decrypt(ciphertext) == original


def test_encrypt_produces_different_ciphertext_each_call(svc):
    # Different nonce each time → different ciphertext
    c1 = svc.encrypt("same-value")
    c2 = svc.encrypt("same-value")
    assert c1 != c2


def test_encrypt_json_roundtrip(svc):
    data = {"api_key": "sk-secret", "token": "tok-123", "nested": {"x": 1}}
    encrypted = svc.encrypt_json(data)
    assert isinstance(encrypted, str)
    decrypted = svc.decrypt_json(encrypted)
    assert decrypted == data


def test_encrypt_json_list(svc):
    data = [1, "two", {"three": 3}]
    assert svc.decrypt_json(svc.encrypt_json(data)) == data


# ── module-level helpers ───────────────────────────────────────────────────────

def test_module_encrypt_decrypt_value():
    ct = encrypt_value("hello world")
    assert decrypt_value(ct) == "hello world"


def test_module_encrypt_decrypt_payload():
    payload = {"provider": "hubspot", "token": "abc123"}
    assert decrypt_payload(encrypt_payload(payload)) == payload


def test_decrypt_tampered_value_raises(svc):
    ct = svc.encrypt("original")
    tampered = ct[:-4] + "XXXX"
    with pytest.raises(Exception):
        svc.decrypt(tampered)
