"""
Sistema de autenticación y autorización militar.
JWT + MFA + RBAC con niveles de habilitación (clearance).
"""
import os
import secrets
import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from functools import wraps

from fastapi import Depends, HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel


# ─────────────────────────────────────────────────────────────────────────────
# Configuración JWT
# ─────────────────────────────────────────────────────────────────────────────
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(64))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Contexto de cifrado de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer(auto_error=False)


# ─────────────────────────────────────────────────────────────────────────────
# Modelos de autenticación
# ─────────────────────────────────────────────────────────────────────────────
class TokenData(BaseModel):
    """Datos contenidos en el JWT."""
    sub: str  # username
    role: str
    clearance: str
    analyst_id: str
    exp: int | None = None


class AnalystCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str = "analyst"
    clearance_level: str = "CONFIDENTIAL"


class AnalystLogin(BaseModel):
    username: str
    password: str
    mfa_token: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades de contraseña
# ─────────────────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Hashea una contraseña con bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades JWT
# ─────────────────────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Crea un JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenData:
    """Decodifica y valida un JWT."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return TokenData(**payload)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido o expirado") from e


# ─────────────────────────────────────────────────────────────────────────────
# MFA (TOTP) - RFC 6238
# ─────────────────────────────────────────────────────────────────────────────
def generate_mfa_secret() -> str:
    """Genera un secreto MFA aleatorio."""
    return secrets.token_hex(20)


def verify_mfa_token(secret: str, token: str) -> bool:
    """
    Verifica un token MFA TOTP.
    En producción usar pyotp: pyotp.TOTP(secret).verify(token)
    """
    # Implementación simplificada para prototipo
    # En producción: import pyotp; return pyotp.TOTP(secret).verify(token)
    return True  # Placeholder


# ─────────────────────────────────────────────────────────────────────────────
# Dependency para obtener usuario actual
# ─────────────────────────────────────────────────────────────────────────────
async def get_current_analyst(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """Obtiene el analista autenticado desde el JWT."""
    if not credentials:
        raise HTTPException(status_code=401, detail="No autorizado")
    return decode_token(credentials.credentials)


# ─────────────────────────────────────────────────────────────────────────────
# Verificación de nivel de habilitación (clearance)
# ─────────────────────────────────────────────────────────────────────────────
CLEARANCE_LEVELS = {
    "CONFIDENTIAL": 1,
    "SECRET": 2,
    "TOP_SECRET": 3,
}


def require_clearance(required_level: str):
    """
    Decorador para verificar nivel de habilitación.
    Uso: @require_clearance("SECRET")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            analyst: TokenData = kwargs.get("current_analyst")
            if not analyst:
                raise HTTPException(status_code=401, detail="No autorizado")
            user_level = CLEARANCE_LEVELS.get(analyst.clearance, 0)
            required = CLEARANCE_LEVELS.get(required_level, 99)
            if user_level < required:
                raise HTTPException(
                    status_code=403,
                    detail=f"Nivel de habilitación insuficiente. Requiere: {required_level}",
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(required_role: str | list[str]):
    """
    Decorador para verificar rol de usuario.
    Uso: @require_role("supervisor") o @require_role(["admin", "supervisor"])
    """
    if isinstance(required_role, str):
        required_role = [required_role]

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            analyst: TokenData = kwargs.get("current_analyst")
            if not analyst:
                raise HTTPException(status_code=401, detail="No autorizado")
            if analyst.role not in required_role:
                raise HTTPException(
                    status_code=403,
                    detail=f"Rol insuficiente. Requiere: {', '.join(required_role)}",
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# HMAC para integridad de logs
# ─────────────────────────────────────────────────────────────────────────────
HMAC_SECRET = os.environ.get("HMAC_SECRET", secrets.token_urlsafe(32))


def generate_hmac(data: str) -> str:
    """Genera firma HMAC-SHA256 para integridad."""
    return hmac.new(
        HMAC_SECRET.encode(),
        data.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_hmac(data: str, signature: str) -> bool:
    """Verifica firma HMAC."""
    expected = generate_hmac(data)
    return hmac.compare_digest(expected, signature)
