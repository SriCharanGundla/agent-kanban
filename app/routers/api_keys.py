"""API Keys Router"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.exceptions import api_key_not_found
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyResponse
from app.services.auth import (
    extract_key_prefix,
    extract_key_suffix,
    generate_api_key,
    hash_api_key,
)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreateResponse:
    """
    Generate a new API key for the current user.

    Requires JWT authentication (web UI only).
    The full API key is returned only once and cannot be retrieved again.
    """
    # Generate the API key
    api_key_value = generate_api_key()
    key_prefix = extract_key_prefix(api_key_value)
    key_suffix = extract_key_suffix(api_key_value)
    key_hash = hash_api_key(api_key_value)

    # Create the API key record
    new_api_key = ApiKey(
        user_id=current_user.id,
        name=api_key_data.name,
        key_prefix=key_prefix,
        key_suffix=key_suffix,
        key_hash=key_hash,
        is_active=True,
        created_at=datetime.now(UTC),
    )

    db.add(new_api_key)
    await db.commit()
    await db.refresh(new_api_key)

    # Return the response with the full API key (only time it's shown)
    return ApiKeyCreateResponse(
        id=new_api_key.id,
        name=new_api_key.name,
        key_prefix=new_api_key.key_prefix,
        key_suffix=new_api_key.key_suffix,
        last_used_at=new_api_key.last_used_at,
        is_active=new_api_key.is_active,
        created_at=new_api_key.created_at,
        expires_at=new_api_key.expires_at,
        key=api_key_value,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
) -> list[ApiKeyResponse]:
    """
    List all API keys for the current user.

    Requires JWT authentication (web UI only).
    """
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == current_user.id, ApiKey.is_active.is_(True))
        .order_by(ApiKey.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    api_keys = result.scalars().all()

    return [
        ApiKeyResponse(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            key_suffix=key.key_suffix,
            last_used_at=key.last_used_at,
            is_active=key.is_active,
            created_at=key.created_at,
            expires_at=key.expires_at,
        )
        for key in api_keys
    ]


@router.delete("/{api_key_id}", status_code=204)
async def revoke_api_key(
    api_key_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Revoke (deactivate) an API key.

    Requires JWT authentication (web UI only).
    The API key must belong to the current user.
    """
    # Get the API key (only if it belongs to the current user and is active)
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == api_key_id,
            ApiKey.user_id == current_user.id,
            ApiKey.is_active.is_(True),
        )
    )
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise api_key_not_found()

    # Deactivate the key (soft revoke)
    api_key.is_active = False
    await db.commit()
