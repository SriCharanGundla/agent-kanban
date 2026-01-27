"""Authentication Router"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.exceptions import email_already_exists, invalid_credentials
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Register a new user account.

    Args:
        user_data: User registration data (email, password, full_name)
        db: Database session

    Returns:
        UserResponse: The created user

    Raises:
        AppException: If email already exists
    """
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise email_already_exists()

    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    Login with email and password to receive JWT token.
    
    Uses OAuth2 password flow (form-urlencoded) for compatibility.

    Args:
        form_data: OAuth2 form data (username=email, password)
        db: Database session

    Returns:
        Token: JWT access token

    Raises:
        AppException: If credentials are invalid
    """
    # Get user by email (username field contains email per OAuth2 spec)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    # Verify user exists, is active, and password is correct
    if (
        not user
        or not user.is_active
        or user.deleted_at is not None
        or not verify_password(form_data.password, user.password_hash)
    ):
        raise invalid_credentials()

    # Create access token
    access_token = create_access_token(user.id)

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
) -> User:
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user (from JWT token)

    Returns:
        UserResponse: Current user information
    """
    return current_user
