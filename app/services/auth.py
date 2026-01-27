"""Authentication Service"""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import settings

# Initialize password hasher with Argon2
pwd_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password using Argon2"""
    return pwd_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: uuid.UUID, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token"""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(UTC) + expires_delta

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(UTC),
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def decode_access_token(token: str) -> uuid.UUID | None:
    """Decode and verify a JWT access token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            return None
        return uuid.UUID(user_id)
    except (jwt.InvalidTokenError, ValueError):
        return None
