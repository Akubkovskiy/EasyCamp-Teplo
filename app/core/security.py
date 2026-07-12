import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Generates a hash from a plain password."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decodes a JWT token. Returns dict or raises error."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except Exception:
        return None


def create_setup_token() -> str:
    """Create a short-lived token that is valid only for the setup wizard."""
    return create_access_token(
        {"scope": "initial_setup", "nonce": secrets.token_urlsafe(16)},
        expires_delta=timedelta(minutes=30),
    )


def verify_setup_token(token: Optional[str]) -> bool:
    if not token:
        return False
    payload = decode_access_token(token)
    return bool(payload and payload.get("scope") == "initial_setup")
