"""
Utilidades de cifrado para protección de datos sensibles.
Cifrado AES-256-GCM (AEAD) para datos en reposo.
"""
import os
import base64
import logging
import hashlib
import hmac
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as _legacy_padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuración de claves (desde variables de entorno)
# ─────────────────────────────────────────────────────────────────────────────
_MASTER_KEY = os.environ.get("VIGIA_MASTER_KEY", None)
_VIGIA_ENV = os.environ.get("VIGIA_ENV", "development").lower()

if _MASTER_KEY is None:
    if _VIGIA_ENV == "production":
        raise RuntimeError(
            "VIGIA_MASTER_KEY no está definida. Es obligatoria en VIGIA_ENV=production."
        )
    logger.critical(
        "PELIGRO: VIGIA_MASTER_KEY no configurada — usando clave de desarrollo INSEGURA. "
        "NUNCA desplegar en producción sin VIGIA_MASTER_KEY definida."
    )
    _MASTER_KEY = hashlib.sha256(b"dev_only_key_never_use_in_production").hexdigest()

# Derivar clave AES de 256 bits
_AES_KEY = hashlib.sha256(_MASTER_KEY.encode()).digest()  # 32 bytes para AES-256

# Tamaño nonce GCM: 12 bytes (recomendación NIST SP 800-38D)
_GCM_NONCE_SIZE = 12


# ─────────────────────────────────────────────────────────────────────────────
# Cifrado AES-256-GCM (AEAD) — formato: base64( nonce(12B) || ciphertext+tag )
# ─────────────────────────────────────────────────────────────────────────────
def encrypt_data(plaintext: str) -> str:
    """
    Cifra un string usando AES-256-GCM.
    Devuelve: base64( nonce(12B) || ciphertext_con_tag )
    """
    if not plaintext:
        return ""

    try:
        aesgcm = AESGCM(_AES_KEY)
        nonce = os.urandom(_GCM_NONCE_SIZE)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")
    except Exception as e:
        logger.error("Error cifrando datos: %s", e)
        raise


def decrypt_data(encrypted_data: str) -> str:
    """
    Descifra un string cifrado con AES-256-GCM.
    Espera: base64( nonce(12B) || ciphertext_con_tag )
    """
    if not encrypted_data:
        return ""

    try:
        raw = base64.b64decode(encrypted_data)
        if len(raw) < _GCM_NONCE_SIZE + 16:
            raise ValueError("Datos cifrados truncados o corruptos")
        nonce = raw[:_GCM_NONCE_SIZE]
        ciphertext = raw[_GCM_NONCE_SIZE:]

        aesgcm = AESGCM(_AES_KEY)
        plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
        return plaintext.decode("utf-8")
    except Exception as e:
        logger.error("Error descifrando datos: %s", e)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Compatibilidad transitoria: descifrar formato antiguo AES-256-CBC
# TODO: eliminar tras migrar todos los registros a GCM (ventana de transición).
# ─────────────────────────────────────────────────────────────────────────────
def decrypt_legacy_cbc(encrypted_data: str) -> str:
    """
    Descifra payloads antiguos en formato AES-256-CBC con PKCS7 padding.
    Formato esperado: base64(iv(16B) || ciphertext).
    Función transitoria — usar solo durante la ventana de migración.
    """
    if not encrypted_data:
        return ""

    try:
        raw = base64.b64decode(encrypted_data)
        if len(raw) < 16:
            raise ValueError("Payload CBC truncado")
        iv = raw[:16]
        ciphertext = raw[16:]

        cipher = Cipher(algorithms.AES(_AES_KEY), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = _legacy_padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        return plaintext.decode("utf-8")
    except Exception as e:
        logger.error("Error descifrando dato legado CBC: %s", e)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# HMAC para integridad de datos
# ─────────────────────────────────────────────────────────────────────────────
_HMAC_KEY = os.environ.get("VIGIA_HMAC_KEY", None)
if _HMAC_KEY is None:
    if _VIGIA_ENV == "production":
        raise RuntimeError(
            "VIGIA_HMAC_KEY no está definida. Es obligatoria en VIGIA_ENV=production."
        )
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
        salt = os.environ.get("VIGIA_HASH_SALT", None)
        if salt is None or salt == "default_salt_change_me":
            if _VIGIA_ENV == "production":
                raise RuntimeError(
                    "VIGIA_HASH_SALT no está definida o usa el valor por defecto. "
                    "Es obligatorio en VIGIA_ENV=production."
                )
            salt = "default_salt_change_me"
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
