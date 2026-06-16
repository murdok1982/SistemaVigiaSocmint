"""
Tests unitarios para src/auth.py.
No requieren servicios externos (Redis, DB, servidor).
"""
import os
import pytest

os.environ.setdefault("VIGIA_ENV", "development")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_for_unit_tests_only_32chars!")

import pyotp

from src.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    decode_access_token,
    generate_mfa_secret,
    verify_mfa_token,
    build_otpauth_url,
    generate_hmac,
    verify_hmac,
    CLEARANCE_LEVELS,
    TokenData,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "SecureP@ssw0rd123!"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct_password")
        assert not verify_password("wrong_password", hashed)

    def test_different_hashes_for_same_password(self):
        password = "misma_contraseña"
        h1 = hash_password(password)
        h2 = hash_password(password)
        assert h1 != h2
        assert verify_password(password, h1)
        assert verify_password(password, h2)

    def test_empty_password_hashes(self):
        hashed = hash_password("")
        assert verify_password("", hashed)


class TestJWTTokens:
    def _base_data(self) -> dict:
        return {
            "sub": "test_user",
            "role": "analyst",
            "clearance": "CONFIDENTIAL",
            "analyst_id": "abc-123",
        }

    def test_access_token_roundtrip(self):
        data = self._base_data()
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded.sub == data["sub"]
        assert decoded.role == data["role"]
        assert decoded.clearance == data["clearance"]
        assert decoded.analyst_id == data["analyst_id"]

    def test_access_token_has_type(self):
        token = create_access_token(self._base_data())
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_refresh_token_roundtrip(self):
        data = self._base_data()
        token, jti = create_refresh_token(data)
        payload = decode_token(token)
        assert payload["type"] == "refresh"
        assert payload["jti"] == jti
        assert payload["sub"] == data["sub"]

    def test_refresh_token_jti_is_unique(self):
        data = self._base_data()
        _, jti1 = create_refresh_token(data)
        _, jti2 = create_refresh_token(data)
        assert jti1 != jti2

    def test_decode_access_rejects_refresh_token(self):
        data = self._base_data()
        token, _ = create_refresh_token(data)
        from fastapi import HTTPException
        with pytest.raises(HTTPException, match="Tipo de token"):
            decode_access_token(token)

    def test_expired_token_raises(self):
        from datetime import timedelta
        from fastapi import HTTPException
        data = self._base_data()
        token = create_access_token(data, expires_delta=timedelta(seconds=-10))
        with pytest.raises(HTTPException):
            decode_access_token(token)


class TestMFA:
    def test_generate_secret_is_base32(self):
        secret = generate_mfa_secret()
        assert len(secret) > 0
        base32_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
        assert all(c in base32_chars for c in secret)

    def test_verify_valid_token(self):
        secret = generate_mfa_secret()
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        assert verify_mfa_token(secret, current_code)

    def test_verify_invalid_token(self):
        secret = generate_mfa_secret()
        assert not verify_mfa_token(secret, "000000")

    def test_verify_empty_inputs(self):
        assert not verify_mfa_token("", "123456")
        assert not verify_mfa_token("secret", "")
        assert not verify_mfa_token("", "")

    def test_build_otpauth_url(self):
        secret = generate_mfa_secret()
        url = build_otpauth_url(username="testuser", secret=secret, issuer="VIGIA")
        assert url.startswith("otpauth://totp/")
        assert "VIGIA" in url
        assert "testuser" in url


class TestHMACAuth:
    def test_roundtrip(self):
        data = "audit log entry"
        sig = generate_hmac(data)
        assert verify_hmac(data, sig)

    def test_tampered_data(self):
        sig = generate_hmac("original data")
        assert not verify_hmac("tampered data", sig)

    def test_consistency(self):
        data = "same input"
        assert generate_hmac(data) == generate_hmac(data)


class TestClearanceLevels:
    def test_ordering(self):
        assert CLEARANCE_LEVELS["CONFIDENTIAL"] < CLEARANCE_LEVELS["SECRET"]
        assert CLEARANCE_LEVELS["SECRET"] < CLEARANCE_LEVELS["TOP_SECRET"]

    def test_all_levels_present(self):
        assert "CONFIDENTIAL" in CLEARANCE_LEVELS
        assert "SECRET" in CLEARANCE_LEVELS
        assert "TOP_SECRET" in CLEARANCE_LEVELS

    def test_comparison(self):
        user_level = CLEARANCE_LEVELS.get("CONFIDENTIAL", 0)
        required = CLEARANCE_LEVELS.get("SECRET", 99)
        assert user_level < required
