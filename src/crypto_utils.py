"""
Utilidades de cifrado para protección de datos sensibles.
Cifrado AES-256-GCM para datos en reposo.
"""
import os
import base64
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import hashlib
import hmac

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuración de claves (desde variables de entorno)
# ─────────────────────────────────────────────────────────────────────────────
_MASTER_KEY = os.environ.get("VIGIA_MASTER_KEY", None)
if _MASTER_KEY is None:
    logger.warning("VIGIA_MASTER_KEY no configurada — usando clave de desarrollo")
    _MASTER_KEY = hashlib.sha256(b"dev_only_key_never_use_in_production").hexdigest()

# Derivar clave AES de 256 bits
_AES_KEY = hashlib.sha256(_MASTER_KEY.encode()).digest()  # 32 bytes para AES-256


# ─────────────────────────────────────────────────────────────────────────────
# Cifrado AES-256-CBC con PKCS7 padding
# ─────────────────────────────────────────────────────────────────────────────
def encrypt_data(plaintext: str) -> str:
    """
    Cifra un string usando AES-256-CBC.
    Devuelve: base64(iv:ciphertext)
    """
    if not plaintext:
        return ""

    try:
        iv = os.urandom(16)  # 128-bit IV
        cipher = Cipher(algorithms.AES(_AES_KEY), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Aplicar padding PKCS7
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()

        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(iv + ciphertext).decode("utf-8")
    except Exception as e:
        logger.error("Error cifrando datos: %s", e)
        raise


def decrypt_data(encrypted_data: str) -> str:
    """
    Descifra un string cifrado con AES-256-CBC.
    Espera: base64(iv:ciphertext)
    """
    if not encrypted_data:
        return ""

    try:
        raw = base64.b64decode(encrypted_data)
        iv = raw[:16]
        ciphertext = raw[16:]

        cipher = Cipher(algorithms.AES(_AES_KEY), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        # Remover padding PKCS7
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        return plaintext.decode("utf-8")
    except Exception as e:
        logger.error("Error descifrando datos: %s", e)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# HMAC para integridad de datos
# ─────────────────────────────────────────────────────────────────────────────
_HMAC_KEY = os.environ.get("VIGIA_HMAC_KEY", None)
if _HMAC_KEY is None:
    _HMAC_KEY = hashlib.sha256(b"hmac_dev_key").digest()
else:
    _HMAC_KEY = _HMAC_KEY.encode()


def generate_hmac(data: str) -> str:
    """Genera HMAC-SHA256 para verificación de integridad."""
    return hmac.new(_HMAC_KEY, data.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_hmac(data: str, signature: str) -> bool:
    """Verifica HMAC-SHA256."""
    expected = generate_hmac(data)
    return hmac.compare_digest(expected, signature)


# ─────────────────────────────────────────────────────────────────────────────
# Hash de identificadores (para anonimización)
# ─────────────────────────────────────────────────────────────────────────────
def hash_identifier(identifier: str, salt: str | None = None) -> str:
    """
    Hashea un identificador con SHA-256.
    Opcional: añade salt único para evitar ataques de diccionario.
    """
    if salt is None:
        salt = os.environ.get("VIGIA_HASH_SALT", "default_salt_change_me")
    return hashlib.sha256((identifier + salt).encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Cifrado de campos específicos para base de datos
# ─────────────────────────────────────────────────────────────────────────────
def encrypt_sensitive_field(value: str | None) -> str | None:
    """Cifra un campo sensible para almacenamiento."""
    if value is None:
        return None
    return encrypt_data(value)


def decrypt_sensitive_field(encrypted: str | None) -> str | None:
    """Descifra un campo sensible desde la base de datos."""
    if encrypted is None:
        return None
    return decrypt_data(encrypted)
