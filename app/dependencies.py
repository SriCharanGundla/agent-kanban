"""FastAPI Dependencies"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import (
    api_key_expired,
    api_key_invalid,
    api_key_invalid_format,
    api_key_required,
    auth_required,
    invalid_token,
    user_inactive,
)
from app.models.api_key import ApiKey
from app.models.user import User
from app.services.auth import decode_access_token, verify_api_key

# HTTP Bearer token scheme for JWT authentication
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials containing the JWT token
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        AppException: If token is invalid or user not found
    """
    if credentials is None:
        raise auth_required()

    token = credentials.credentials

    # Decode the JWT token
    user_id = decode_access_token(token)
    if user_id is None:
        raise invalid_token()

    # Get the user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active or user.deleted_at is not None:
        raise user_inactive()

    return user


async def get_current_user_from_api_key(
    x_api_key: Annotated[str | None, Header()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency to get the current authenticated user from API key.

    Args:
        x_api_key: API key from X-API-Key header
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        AppException: If API key is invalid or inactive
    """
    if x_api_key is None:
        raise api_key_required()

    # Validate API key format
    if not x_api_key.startswith("ak_"):
        raise api_key_invalid_format()

    # Extract prefix for lookup (first 12 chars total)
    key_prefix = x_api_key[:12]

    # Query API keys with this prefix
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_prefix == key_prefix, ApiKey.is_active)
    )
    api_keys = result.scalars().all()

    # Try to verify the key using constant-time comparison
    # Note: We check all candidates (no early break) for constant-time behavior
    matched_key = None
    for api_key in api_keys:
        if verify_api_key(x_api_key, api_key.key_hash):
            matched_key = api_key

    if matched_key is None:
        raise api_key_invalid()

    # Check expiration
    if matched_key.expires_at:
        # Ensure timezone-aware comparison (SQLite returns naive datetimes)
        expires_at = (
            matched_key.expires_at.replace(tzinfo=UTC)
            if matched_key.expires_at.tzinfo is None
            else matched_key.expires_at
        )
        if expires_at < datetime.now(UTC):
            raise api_key_expired()

    # Update last_used_at timestamp (will be committed by get_db at request end)
    matched_key.last_used_at = datetime.now(UTC)

    # Get the user
    result = await db.execute(select(User).where(User.id == matched_key.user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active or user.deleted_at is not None:
        raise user_inactive()

    return user


async def get_current_user_flexible(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: Annotated[str | None, Header()] = None,
) -> User:
    """
    Dependency to get the current authenticated user from either JWT or API key.

    Accepts either:
    - Bearer token in Authorization header (JWT)
    - API key in X-API-Key header

    Args:
        credentials: HTTP Bearer credentials (optional)
        x_api_key: API key from header (optional)
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        AppException: If authentication fails
    """
    # Try JWT first if present
    if credentials:
        token = credentials.credentials
        user_id = decode_access_token(token)
        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user and user.is_active and user.deleted_at is None:
                return user

    # Try API key if present
    if x_api_key:
        return await get_current_user_from_api_key(x_api_key, db)

    # No valid authentication provided
    raise auth_required()


# Type annotations for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserFlexible = Annotated[User, Depends(get_current_user_flexible)]
