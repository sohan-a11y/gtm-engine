"""Unit tests for backend/core/auth.py"""
from __future__ import annotations

import pytest

from backend.core.auth import (
    TokenBundle,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    hash_password,
    token_fingerprint,
    token_jti,
    verify_password,
)
from backend.core.exceptions import AuthenticationError


# ── password hashing ──────────────────────────────────────────────────────────

def test_hash_and_verify_password():
    hashed = hash_password("super-secret")
    assert hashed != "super-secret"
    assert verify_password("super-secret", hashed)


def test_verify_wrong_password_returns_false():
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False


def test_verify_invalid_hash_returns_false():
    assert verify_password("anything", "not-a-real-hash") is False


# ── access token ──────────────────────────────────────────────────────────────

def test_create_and_decode_access_token():
    token = create_access_token("user-1", "org-1", "admin", ["leads:read"])
    payload = decode_token(token, expected_type="access")
    assert payload.sub == "user-1"
    assert payload.org_id == "org-1"
    assert payload.role == "admin"
    assert "leads:read" in payload.permissions
    assert payload.type == "access"


def test_access_token_has_jti():
    token = create_access_token("u", "o", "member", [])
    payload = decode_token(token)
    assert payload.jti  # non-empty


def test_decode_wrong_type_raises():
    refresh = create_refresh_token("u", "o")
    with pytest.raises(AuthenticationError):
        decode_token(refresh, expected_type="access")


# ── refresh token ─────────────────────────────────────────────────────────────

def test_create_and_decode_refresh_token():
    token = create_refresh_token("user-2", "org-2")
    payload = decode_token(token, expected_type="refresh")
    assert payload.sub == "user-2"
    assert payload.org_id == "org-2"
    assert payload.type == "refresh"


# ── token pair ────────────────────────────────────────────────────────────────

def test_create_token_pair_returns_bundle():
    bundle = create_token_pair("u", "o", "viewer", ["leads:read"])
    assert isinstance(bundle, TokenBundle)
    assert bundle.token_type == "bearer"
    assert bundle.access_token
    assert bundle.refresh_token
    assert bundle.expires_in > 0


# ── helpers ───────────────────────────────────────────────────────────────────

def test_token_jti_is_non_empty():
    token = create_access_token("u", "o", "admin", [])
    assert token_jti(token)


def test_token_fingerprint_is_deterministic():
    token = create_access_token("u", "o", "admin", [])
    fp1 = token_fingerprint(token)
    fp2 = token_fingerprint(token)
    assert fp1 == fp2
    assert len(fp1) > 20


def test_token_fingerprint_differs_for_different_tokens():
    t1 = create_access_token("u1", "o", "admin", [])
    t2 = create_access_token("u2", "o", "admin", [])
    assert token_fingerprint(t1) != token_fingerprint(t2)


def test_decode_garbage_raises():
    with pytest.raises(Exception):
        decode_token("not.a.valid.token")
