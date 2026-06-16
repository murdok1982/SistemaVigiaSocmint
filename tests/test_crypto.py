"""
Tests unitarios para src/crypto_utils.py.
No requieren servicios externos (Redis, DB, servidor).
"""
import os
import pytest

os.environ.setdefault("VIGIA_ENV", "development")
os.environ.setdefault("VIGIA_MASTER_KEY", "test_master_key_for_unit_tests_only")
os.environ.setdefault("VIGIA_HMAC_KEY", "test_hmac_key_for_unit_tests_only")
os.environ.setdefault("VIGIA_HASH_SALT", "test_salt_for_unit_tests")

from src.crypto_utils import (
    encrypt_data,
    decrypt_data,
    hash_identifier,
    generate_hmac,
    verify_hmac,
    encrypt_sensitive_field,
    decrypt_sensitive_field,
)


class TestEncryptDecryptRoundtrip:
    def test_basic_roundtrip(self):
        plaintext = "Hola mundo"
        encrypted = encrypt_data(plaintext)
        assert encrypted != plaintext
        assert decrypt_data(encrypted) == plaintext

    def test_empty_string(self):
        assert encrypt_data("") == ""
        assert decrypt_data("") == ""

    def test_unicode_content(self):
        plaintext = "Ñoño — señalización «clasificada»"
        encrypted = encrypt_data(plaintext)
        assert decrypt_data(encrypted) == plaintext

    def test_long_content(self):
        plaintext = "A" * 100_000
        encrypted = encrypt_data(plaintext)
        assert decrypt_data(encrypted) == plaintext

    def test_different_encryptions_differ(self):
        plaintext = "mismo texto"
        e1 = encrypt_data(plaintext)
        e2 = encrypt_data(plaintext)
        assert e1 != e2

    def test_tampered_ciphertext_raises(self):
        encrypted = encrypt_data("secreto")
        raw = bytearray(encrypted.encode())
        raw[-1] ^= 0xFF
        with pytest.raises(Exception):
            decrypt_data(raw.decode())


class TestSensitiveFieldRoundtrip:
    def test_none_passthrough(self):
        assert encrypt_sensitive_field(None) is None
        assert decrypt_sensitive_field(None) is None

    def test_roundtrip(self):
        value = "campo sensible"
        assert decrypt_sensitive_field(encrypt_sensitive_field(value)) == value


class TestHashIdentifier:
    def test_consistency(self):
        h1 = hash_identifier("user_123")
        h2 = hash_identifier("user_123")
        assert h1 == h2

    def test_different_inputs_differ(self):
        h1 = hash_identifier("user_123")
        h2 = hash_identifier("user_456")
        assert h1 != h2

    def test_custom_salt(self):
        h1 = hash_identifier("user_123", salt="salt_a")
        h2 = hash_identifier("user_123", salt="salt_b")
        assert h1 != h2

    def test_output_is_hex_sha256(self):
        h = hash_identifier("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestHMAC:
    def test_roundtrip(self):
        data = "log entry data"
        sig = generate_hmac(data)
        assert verify_hmac(data, sig)

    def test_tampered_data_fails(self):
        sig = generate_hmac("original")
        assert not verify_hmac("modified", sig)

    def test_tampered_sig_fails(self):
        sig = generate_hmac("data")
        bad = sig[:-2] + "ff"
        assert not verify_hmac("data", bad)

    def test_consistency(self):
        data = "mismo contenido"
        assert generate_hmac(data) == generate_hmac(data)
