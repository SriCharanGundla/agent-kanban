"""FastAPI Dependencies"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
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
        HTTPException: If token is invalid or user not found
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials

    # Decode the JWT token
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get the user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
        HTTPException: If API key is invalid or inactive
    """
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": 'ApiKey realm="API Key"'},
        )

    # Validate API key format
    if not x_api_key.startswith("ak_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
        )

    # Check expiration
    if matched_key.expires_at and matched_key.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Update last_used_at timestamp (will be committed by get_db at request end)
    matched_key.last_used_at = datetime.now(UTC)

    # Get the user
    result = await db.execute(select(User).where(User.id == matched_key.user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def get_current_user_flexible(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    x_api_key: Annotated[str | None, Header()],
    db: Annotated[AsyncSession, Depends(get_db)],
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
        HTTPException: If authentication fails
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
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (Bearer token or API key)",
        headers={"WWW-Authenticate": 'Bearer, ApiKey realm="API Key"'},
    )


# Type annotations for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserFlexible = Annotated[User, Depends(get_current_user_flexible)]
