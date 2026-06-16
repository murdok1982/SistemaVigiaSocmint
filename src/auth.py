"""
Sistema de autenticación y autorización militar.
JWT + MFA TOTP (RFC 6238) + RBAC con niveles de habilitación (clearance).
"""
import os
import secrets
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps

import pyotp
from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel


# ─────────────────────────────────────────────────────────────────────────────
# Configuración JWT
# ─────────────────────────────────────────────────────────────────────────────
ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"

_VIGIA_ENV = os.environ.get("VIGIA_ENV", "development").lower()
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", None)
if JWT_SECRET_KEY is None:
    if _VIGIA_ENV == "production":
        raise RuntimeError(
            "JWT_SECRET_KEY no está definida. Es obligatoria en VIGIA_ENV=production."
        )
    JWT_SECRET_KEY = secrets.token_urlsafe(64)
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


def create_refresh_token(data: dict) -> tuple[str, str]:
    """
    Crea un JWT refresh token con jti único.
    Devuelve: (token_codificado, jti). El jti debe persistirse en Redis para
    permitir rotación y revocación.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
    encoded = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded, jti


def decode_token(token: str) -> dict:
    """Decodifica y valida un JWT y devuelve el payload completo (dict)."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido o expirado") from e


def decode_access_token(token: str) -> TokenData:
    """Decodifica un access token y devuelve TokenData tipado."""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Tipo de token inválido")
    return TokenData(**{k: v for k, v in payload.items() if k in TokenData.model_fields})


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Establece cookies HttpOnly para access y refresh tokens."""
    is_prod = _VIGIA_ENV == "production"
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )


def clear_auth_cookies(response: Response) -> None:
    """Borra las cookies de autenticación."""
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path="/")


async def get_token_from_cookie_or_header(request: Request) -> str | None:
    """Obtiene el token desde Authorization header o cookie. Prioriza header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.cookies.get(ACCESS_TOKEN_COOKIE)


# ─────────────────────────────────────────────────────────────────────────────
# MFA (TOTP) - RFC 6238 — implementación real con pyotp
# ─────────────────────────────────────────────────────────────────────────────
def generate_mfa_secret() -> str:
    """Genera un secreto MFA en base32 (compatible con pyotp/Google Authenticator)."""
    return pyotp.random_base32()


def verify_mfa_token(secret: str, token: str) -> bool:
    """
    Verifica un código TOTP (RFC 6238) con ventana de tolerancia ±30s.
    """
    if not secret or not token:
        return False
    try:
        return pyotp.TOTP(secret).verify(token, valid_window=1)
    except Exception:
        return False


def build_otpauth_url(username: str, secret: str, issuer: str = "VIGIA") -> str:
    """Construye la URL otpauth:// para enrolar en una app autenticadora."""
    return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)


# ─────────────────────────────────────────────────────────────────────────────
# Dependency para obtener usuario actual
# ─────────────────────────────────────────────────────────────────────────────
async def get_current_analyst(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None,
) -> TokenData:
    """Obtiene el analista autenticado desde header JWT o cookie HttpOnly."""
    token = None
    if credentials:
        token = credentials.credentials
    elif request:
        token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="No autorizado")
    return decode_access_token(token)


# ─────────────────────────────────────────────────────────────────────────────
# Verificación de nivel de habilitación (clearance)
# ─────────────────────────────────────────────────────────────────────────────
CLEARANCE_LEVELS = {
    "CONFIDENTIAL": 1,
    "SECRET": 2,
    "TOP_SECRET": 3,
}


def require_clearance(required_level: str, param: str = "current"):
    """
    Decorador para verificar nivel de habilitación.
    Uso: @require_clearance("SECRET") o @require_clearance("SECRET", param="current_analyst")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            analyst: TokenData = kwargs.get(param)
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


def require_role(required_role: str | list[str], param: str = "current"):
    """
    Decorador para verificar rol de usuario.
    Uso: @require_role("supervisor") o @require_role(["admin", "supervisor"])
    """
    if isinstance(required_role, str):
        required_role = [required_role]

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            analyst: TokenData = kwargs.get(param)
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
HMAC_SECRET = os.environ.get("HMAC_SECRET", None)
if HMAC_SECRET is None:
    if _VIGIA_ENV == "production":
        raise RuntimeError(
            "HMAC_SECRET no está definida. Es obligatoria en VIGIA_ENV=production."
        )
    HMAC_SECRET = secrets.token_urlsafe(32)


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
