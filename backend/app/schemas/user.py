"""User Pydantic Schemas"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user"""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login (OAuth2 compatible)"""

    username: EmailStr  # OAuth2 spec uses 'username'
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile"""

    full_name: str | None = Field(None, min_length=1, max_length=255)


class UserResponse(BaseModel):
    """Schema for user response"""

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT token response"""

    access_token: str
    token_type: str = "bearer"
