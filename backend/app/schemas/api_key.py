"""API Key Pydantic Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    """Schema for creating a new API key"""

    name: str = Field(..., min_length=1, max_length=255, description="Descriptive name for the API key")


class ApiKeyResponse(BaseModel):
    """Schema for API key in list view (no full key)"""

    id: UUID
    name: str
    key_prefix: str
    key_suffix: str | None = None
    last_used_at: datetime | None
    is_active: bool
    created_at: datetime
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class ApiKeyCreateResponse(ApiKeyResponse):
    """Schema for API key creation response (includes full key once)"""

    key: str = Field(..., description="Full API key - shown only once!")
